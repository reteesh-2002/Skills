#!/usr/bin/env python3
"""
Antigravity Skill Validator
Zero-dependency validator for skill directory conventions, YAML frontmatter,
context token budgets, and relative file references.
"""

import json
import re
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".github", ".agents", ".evidence", "scripts", "tests",
    "docs", "Reports", "reports", "__pycache__", "node_modules", "vendor"
}

def parse_frontmatter(content: str):
    """Extract and parse YAML frontmatter between leading --- delimiters."""
    content = content.lstrip("\ufeff")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, content
    raw_fm = match.group(1)
    body = content[match.end():]

    data = {}
    current_key = None
    multiline_lines = []

    for line in raw_fm.splitlines():
        # Check if line is indented continuation (or blank line inside) a multiline scalar
        if current_key and (line.startswith("  ") or line.startswith("\t") or not line.strip()):
            if line.strip():
                multiline_lines.append(line.strip())
            continue
        elif current_key:
            data[current_key] = " ".join(multiline_lines)
            current_key = None
            multiline_lines = []

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Ignore indented nested mapping keys so they don't overwrite top-level keys
        if line.startswith((" ", "\t")):
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in ("|", ">", "|-", ">-"):
                current_key = key
                multiline_lines = []
            else:
                data[key] = val.strip("'\"")

    if current_key:
        data[current_key] = " ".join(multiline_lines)

    return data, body

def check_relative_links(skill_dir: Path, skill_file: Path, body: str, repo_root: Path | None = None) -> list[str]:
    """Verify that relative markdown links point to existing files on disk."""
    errors = []

    # Strip 4-backtick and 3-backtick fenced code blocks so code examples aren't treated as real links
    clean_body = re.sub(r"````[\s\S]*?````", "", body)
    clean_body = re.sub(r"```[\s\S]*?```", "", clean_body)
    # Strip inline code spans that themselves contain markdown link syntax (e.g., `![alt](./x.png)`)
    clean_body = re.sub(r"`[^`\n]*\[[^\]]+\]\([^)]+\)[^`\n]*`", "", clean_body)

    # Match markdown links [text](target "optional title")
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    resolved_root = repo_root.resolve() if repo_root else None
    for match in link_pattern.finditer(clean_body):
        raw_target = match.group(2).strip()
        # Strip optional title ("..." or '...')
        raw_target = re.sub(r"""\s+["'][^"']*["']\s*$""", "", raw_target)
        link_target = raw_target.split("#")[0].split("?")[0].strip()
        if not link_target:
            continue
        # Skip external schemes and pseudo-URIs
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link_target):
            continue

        target_path = (skill_file.parent / link_target).resolve()
        if resolved_root and not target_path.is_relative_to(resolved_root):
            errors.append(f"Relative link escapes repository root in {skill_file.name}: '{link_target}'")
            continue
        if not target_path.exists():
            errors.append(f"Broken relative link in {skill_file.name}: '{link_target}' (resolved to {target_path})")

    return errors


def check_policy_parity(repo_root: Path, discovered_skills: list[str]) -> list[str]:
    """Verify suite-policy.json exists, is valid JSON, and matches discovered skill directories."""
    policy_path = repo_root / "suite-policy.json"
    if not policy_path.exists():
        return ["suite-policy.json not found — cannot validate policy parity"]
    try:
        with open(policy_path, encoding="utf-8") as f:
            policy = json.load(f)
    except Exception as e:
        return [f"suite-policy.json is not valid JSON: {e}"]

    explicit_list = policy.get("activation_modes", {}).get("explicit_only", [])
    auto_entries = policy.get("activation_modes", {}).get("auto", [])
    explicit_only = set(explicit_list)
    auto_skills = set()
    errors = []
    for entry in auto_entries:
        if not isinstance(entry, dict) or "skill" not in entry:
            errors.append(f"Malformed auto activation entry in suite-policy.json: {entry!r}")
            continue
        auto_skills.add(entry["skill"])

    overlap = sorted(explicit_only & auto_skills)
    if overlap:
        errors.append(f"suite-policy.json lists skill(s) in both auto and explicit_only: {', '.join(overlap)}")

    policy_skills = explicit_only | auto_skills
    disk_skills = set(discovered_skills)

    for missing in sorted(policy_skills - disk_skills):
        errors.append(f"suite-policy.json lists '{missing}' but directory does not exist")
    for extra in sorted(disk_skills - policy_skills):
        errors.append(f"Skill directory '{extra}' is missing from suite-policy.json")
    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    errors = []
    skills = []

    skills_subdir = repo_root / "skills"
    search_dirs = [skills_subdir] if (skills_subdir.exists() and skills_subdir.is_dir()) else [repo_root]

    for base in search_dirs:
        for entry in sorted(base.iterdir()):
            if not entry.is_dir() or entry.name in IGNORED_DIRS or entry.name.startswith("."):
                continue
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            skills.append(entry)

    print(f"🔍 Validating {len(skills)} Antigravity skills in {repo_root}...\n")
    print(f"{'Skill Name':<32} {'Tokens':<10} {'Size':<10} {'Status'}")
    print("-" * 65)

    min_tokens = 150
    max_tokens = 1500
    policy_file = repo_root / "suite-policy.json"
    if policy_file.is_file():
        try:
            policy_data = json.loads(policy_file.read_text(encoding="utf-8"))
            target_cfg = policy_data.get("token_targets", {}).get("ordinary_entrypoints_estimated_tokens", {})
            if isinstance(target_cfg, dict):
                min_tokens = int(target_cfg.get("min", min_tokens))
                max_tokens = int(target_cfg.get("max", max_tokens))
            elif isinstance(target_cfg, (int, float)):
                max_tokens = int(target_cfg)
            else:
                errors.append("[suite-policy.json] Invalid token_targets.ordinary_entrypoints_estimated_tokens type")
        except (ValueError, TypeError) as e:
            errors.append(f"[suite-policy.json] Invalid token_targets configuration: {e}")
        except Exception as e:
            errors.append(f"[suite-policy.json] Failed to parse token_targets: {e}")

    for skill_dir in skills:
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        size_bytes = len(content.encode("utf-8"))
        words = len(content.split())
        est_tokens = int(words * 1.3)

        fm, body = parse_frontmatter(content)
        skill_errors = []

        if not fm:
            skill_errors.append("Missing or invalid YAML frontmatter delimiters (---)")
        else:
            name = fm.get("name")
            desc = fm.get("description")

            if not name:
                skill_errors.append("Frontmatter missing 'name'")
            elif name != skill_dir.name:
                skill_errors.append(f"Frontmatter name '{name}' does not match directory '{skill_dir.name}'")
            elif not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
                skill_errors.append(f"Skill name '{name}' must be lowercase kebab-case")

            if not desc:
                skill_errors.append("Frontmatter missing 'description'")
            elif len(desc) < 20:
                skill_errors.append(f"Description is too brief ({len(desc)} characters, minimum 20)")

        link_errors = check_relative_links(skill_dir, skill_file, body, repo_root=repo_root)
        skill_errors.extend(link_errors)

        if est_tokens < min_tokens:
            skill_errors.append(f"SKILL.md is below minimum token budget ({est_tokens} < {min_tokens})")
        elif est_tokens > max_tokens:
            skill_errors.append(f"SKILL.md exceeds token budget ({est_tokens} > {max_tokens})")

        stale_patterns = (
            "exec_proxy", "exec-proxy.sh", "Exec Proxy", "Execute via Proxy",
            "verify_release_gate", "verify-release-gate.sh",
            "specialist_probes.py", "task_ledger.py", "task_shape_gating.py",
            "slice-guard.py", "audit_diff", "setup_worktrees", "guard_read_before_write",
            "probe_memory_soak_plateau", "probe_graceful_drain_subprocess",
            ".evidence/manifest.v1.json", "manifest-receipt.v1", "update_manifest",
            "evaluate_release_gate", "anti-slop-spec.v1", "adaptive-worker-orchestrator-v2",
            "openai.yaml", "rcpt_id",
        )
        files_to_scan = [skill_file]
        refs_dir = skill_dir / "references"
        if refs_dir.is_dir():
            ref_mds = sorted(refs_dir.rglob("*.md"))
            files_to_scan.extend(ref_mds)
            skill_text_norm = content.replace("\\", "/")
            for ref_md in ref_mds:
                link_errors_ref = check_relative_links(skill_dir, ref_md, ref_md.read_text(encoding="utf-8"), repo_root=repo_root)
                skill_errors.extend(link_errors_ref)
                rel_ref = ref_md.relative_to(skill_dir).as_posix()
                if rel_ref not in skill_text_norm:
                    skill_errors.append(f"Orphaned reference file not linked from SKILL.md: {rel_ref}")
        for scan_file in files_to_scan:
            scan_text = scan_file.read_text(encoding="utf-8")
            for pat in stale_patterns:
                if pat in scan_text:
                    skill_errors.append(f"Stale deleted reference '{pat}' in {scan_file.relative_to(skill_dir)}")

        if skill_errors:
            status = "❌ FAIL"
            errors.extend([f"[{skill_dir.name}] {e}" for e in skill_errors])
        else:
            status = "✅ PASS"

        print(f"{skill_dir.name:<32} ~{est_tokens:<9} {size_bytes:>6} B   {status}")

    print("-" * 65)

    # Policy parity check
    drift_errors = check_policy_parity(repo_root, [s.name for s in skills])
    if drift_errors:
        print("\n⚠️  Policy parity errors detected:")
        for err in drift_errors:
            print(f"  - {err}")
        errors.extend(drift_errors)

    # Root docs stale-reference scan & link checks (exclude CHANGELOG.md, which documents historical removals)
    output_policy_path = (
        skills_subdir / "references" / "output-policy.md"
        if skills_subdir.is_dir()
        else repo_root / "references" / "output-policy.md"
    )
    root_docs = [
        repo_root / "README.md",
        repo_root / "REQUIREMENTS.md",
        repo_root / "CONTRIBUTING.md",
        repo_root / "AGENTS.md",
        repo_root / "GEMINI.md",
        repo_root / "suite-policy.json",
        output_policy_path,
    ]
    link_checked_docs = {
        repo_root / "AGENTS.md",
        repo_root / "GEMINI.md",
        output_policy_path,
    }
    for doc in root_docs:
        if doc.is_file():
            doc_text = doc.read_text(encoding="utf-8")
            for pat in stale_patterns:
                if pat in doc_text:
                    errors.append(f"[{doc.relative_to(repo_root)}] Stale deleted reference '{pat}'")
            if doc in link_checked_docs:
                errors.extend(check_relative_links(repo_root, doc, doc_text, repo_root=repo_root))

    hooks_file = repo_root / ".agents" / "hooks.json"
    if hooks_file.is_file():
        try:
            hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
            ep = hooks_data.get("evidence-policy") if isinstance(hooks_data, dict) else None
            if not (isinstance(ep, dict) and isinstance(ep.get("PreToolUse"), list) and isinstance(ep.get("PostToolUse"), list)):
                errors.append("[.agents/hooks.json] Invalid or missing 'evidence-policy' PreToolUse/PostToolUse schema")
        except Exception as e:
            errors.append(f"[.agents/hooks.json] Invalid JSON: {e}")

    if errors:
        print(f"\n❌ Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(skills)} skills successfully validated with zero defects!")
        sys.exit(0)

if __name__ == "__main__":
    main()

