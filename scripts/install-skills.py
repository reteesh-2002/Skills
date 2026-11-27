#!/usr/bin/env python3
"""
Antigravity Skills Suite — Installer and Manifest Manager
Installs an explicit skill and runtime inventory, safe-merges hooks and rules,
and tracks an install manifest (.skills-install-manifest.json) for clean updates and uninstallation.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys

def load_skill_inventory() -> list[str]:
    """Load the authoritative skill roster from suite-policy.json."""
    policy_path = Path(__file__).resolve().parent.parent / "suite-policy.json"
    if policy_path.exists():
        data = json.loads(policy_path.read_text(encoding="utf-8"))
        auto = [e["skill"] for e in data.get("activation_modes", {}).get("auto", [])]
        explicit = data.get("activation_modes", {}).get("explicit_only", [])
        return auto + explicit
    return []


# Authoritative suite skill inventory loaded from suite-policy.json
SKILL_INVENTORY = load_skill_inventory()

# Explicit runtime inventory scripts and policies
RUNTIME_SCRIPTS = [
    "scripts/guard_anti_retry.py",
    "scripts/validate-skills.py",
    "scripts/skills-doctor.py",
]

POLICY_FILES = [
    "suite-policy.json",
]

RULE_FILES = [
    "AGENTS.md",
    "GEMINI.md",
]

def _portable_hook_command() -> str:
    python_cmd = "python3" if shutil.which("python3") and sys.platform != "win32" else "python"
    return (
        f"{python_cmd} -c \"import json,pathlib,runpy; rel='scripts/guard_anti_retry.py'; "
        "cands=[d/rel for d in [pathlib.Path.cwd(),*pathlib.Path.cwd().parents]]+"
        "[pathlib.Path.home()/'.gemini'/sub/rel for sub in ('config','antigravity')]; "
        "hit=next((p for p in cands if p.is_file()),None); "
        "runpy.run_path(str(hit),run_name='__main__') if hit else print(json.dumps({'decision':'allow'}))\""
    )

def get_default_hook_template():
    # Pure Python is cross-platform across Windows, Linux, and macOS
    hook_cmd = _portable_hook_command()
    return {
        "evidence-policy": {
            "description": "Lightweight safety invariants (Anti-Retry and mutation hygiene)",
            "PreToolUse": [
                {
                    "matcher": "run_command",
                    "description": "Enforce Anti-Exact-Retry invariant to halt runaway failure loops",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_cmd,
                            "timeout": 5,
                        }
                    ],
                },
            ],
            "PostToolUse": [
                {
                    "matcher": "*",
                    "description": "Record tool failures and clear failures on successful edits for Anti-Exact-Retry",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_cmd,
                            "timeout": 5,
                        }
                    ],
                },
            ],
        }
    }

HOOK_TEMPLATE = get_default_hook_template()

MANIFEST_FILENAME = ".skills-install-manifest.json"
RULES_MARKER_START = "<!-- BEGIN ANTIGRAVITY SKILLS SUITE RULES -->"
RULES_MARKER_END = "<!-- END ANTIGRAVITY SKILLS SUITE RULES -->"


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_repo_root() -> Path:
    """Locate the root of the source Skills repository."""
    # First check this script's directory parent
    script_parent = Path(__file__).resolve().parent.parent
    if (script_parent / "suite-policy.json").exists() and (script_parent / "plan-master").exists():
        return script_parent
    # Fallback to current working directory if it is the repo root
    cwd = Path.cwd().resolve()
    if (cwd / "suite-policy.json").exists() and (cwd / "plan-master").exists():
        return cwd
    return script_parent


def copy_skill(
    skill_name: str,
    src_dir: Path,
    dest_skills_dir: Path,
    dest_root: Path,
    manifest_files: dict,
    verbose: bool = False,
):
    """Copy a single skill directory and record its files in the manifest."""
    src_skill = src_dir / skill_name
    if not src_skill.exists() or not src_skill.is_dir():
        if verbose:
            print(f"⚠️  Skill directory not found in source: {src_skill}")
        return

    dest_skill = dest_skills_dir / skill_name
    dest_skill.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(src_skill):
        # Skip cache and internal VCS folders
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".pytest_cache", ".git"}]
        root_path = Path(root)
        rel_to_skill = root_path.relative_to(src_skill)
        target_dir = dest_skill / rel_to_skill
        target_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            if file.endswith((".pyc", ".pyo", ".pyd")) or file in {".DS_Store"}:
                continue
            src_file = root_path / file
            dest_file = target_dir / file
            if src_file.resolve() != dest_file.resolve():
                shutil.copy2(src_file, dest_file)
            rel_manifest_path = dest_file.relative_to(dest_root).as_posix()
            manifest_files[rel_manifest_path] = {
                "action": "created",
                "sha256": compute_sha256(dest_file),
            }


def copy_runtime_file(
    src_file: Path,
    dest_file: Path,
    dest_root: Path,
    manifest_files: dict,
    verbose: bool = False,
):
    """Copy a runtime file and ensure executable permissions for scripts."""
    if not src_file.exists():
        if verbose:
            print(f"⚠️  Runtime file not found in source: {src_file}")
        return

    dest_file.parent.mkdir(parents=True, exist_ok=True)
    if src_file.resolve() != dest_file.resolve():
        shutil.copy2(src_file, dest_file)

    if dest_file.suffix in {".sh", ".py"}:
        try:
            curr_mode = dest_file.stat().st_mode
            dest_file.chmod(curr_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

    rel_manifest_path = dest_file.relative_to(dest_root).as_posix()
    manifest_files[rel_manifest_path] = {
        "action": "created",
        "sha256": compute_sha256(dest_file),
    }


def _normalize_hook_commands(data: dict) -> dict:
    """Ensure hook commands use a cross-platform Python executable."""
    if sys.platform != "win32" and shutil.which("python3"):
        return data
    ep = data.get("evidence-policy")
    if isinstance(ep, dict):
        for phase in ("PreToolUse", "PostToolUse"):
            entries = ep.get(phase)
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
                        for h in entry["hooks"]:
                            if isinstance(h, dict) and isinstance(h.get("command"), str) and h["command"].startswith("python3 -c "):
                                h["command"] = "python -c " + h["command"][len("python3 -c "):]
    return data


def safe_merge_hooks(
    src_hooks_file: Path,
    dest_hooks_file: Path,
    dest_root: Path,
    manifest_files: dict,
    existing_manifest_files: dict,
    verbose: bool = False,
):
    """Safely merge hooks into dest_hooks_file without overwriting user configuration."""
    rel_path = dest_hooks_file.relative_to(dest_root).as_posix()

    # Load source hook data
    if src_hooks_file.exists():
        try:
            src_data = json.loads(src_hooks_file.read_text(encoding="utf-8"))
            if not isinstance(src_data, dict):
                src_data = HOOK_TEMPLATE
        except Exception:
            src_data = HOOK_TEMPLATE
    else:
        src_data = HOOK_TEMPLATE
    src_data = _normalize_hook_commands(json.loads(json.dumps(src_data)))

    dest_hooks_file.parent.mkdir(parents=True, exist_ok=True)

    if dest_hooks_file.exists():
        existing_text = dest_hooks_file.read_text(encoding="utf-8")
        try:
            dest_data = json.loads(existing_text)
            if not isinstance(dest_data, dict):
                dest_data = {}
        except Exception:
            if verbose:
                print(f"⚠️  Existing {dest_hooks_file} is invalid JSON; replacing while preserving original_content in manifest.")
            dest_data = {}

        # Preserve original_content from previous manifest if available
        prior_info = existing_manifest_files.get(rel_path, {})
        prior_action = prior_info.get("action")
        original_content = prior_info.get("original_content", existing_text)

        added_keys = []
        for k, v in src_data.items():
            dest_data[k] = v
            added_keys.append(k)

        dest_hooks_file.write_text(json.dumps(dest_data, indent=2) + "\n", encoding="utf-8")

        # If it was created by us in a prior run, it stays "created" so uninstall removes it
        action = "created" if prior_action == "created" else "merged"
        manifest_files[rel_path] = {
            "action": action,
            "sha256": compute_sha256(dest_hooks_file),
            "original_content": original_content,
            "added_keys": added_keys,
        }
    else:
        dest_hooks_file.write_text(json.dumps(src_data, indent=2) + "\n", encoding="utf-8")
        manifest_files[rel_path] = {
            "action": "created",
            "sha256": compute_sha256(dest_hooks_file),
            "added_keys": list(src_data.keys()),
        }


def safe_merge_rules(
    src_rule_file: Path,
    dest_rule_file: Path,
    dest_root: Path,
    manifest_files: dict,
    existing_manifest_files: dict,
    verbose: bool = False,
):
    """Safely merge rules into AGENTS.md / GEMINI.md with markers preserving user content."""
    rel_path = dest_rule_file.relative_to(dest_root).as_posix()
    if not src_rule_file.exists():
        return

    rule_text = src_rule_file.read_text(encoding="utf-8").strip()
    if dest_rule_file.parent == dest_root:
        rule_text = rule_text.replace("(references/output-policy.md)", "(skills/references/output-policy.md)")
    marked_block = f"{RULES_MARKER_START}\n{rule_text}\n{RULES_MARKER_END}"

    dest_rule_file.parent.mkdir(parents=True, exist_ok=True)

    if dest_rule_file.exists():
        existing_text = dest_rule_file.read_text(encoding="utf-8")

        prior_info = existing_manifest_files.get(rel_path, {})
        prior_action = prior_info.get("action")
        original_content = prior_info.get("original_content", existing_text)

        # Check if markers exist
        if RULES_MARKER_START in existing_text and RULES_MARKER_END in existing_text:
            pattern = re.compile(
                rf"{re.escape(RULES_MARKER_START)}[\s\S]*?{re.escape(RULES_MARKER_END)}"
            )
            new_text = pattern.sub(lambda _m: marked_block, existing_text)
        elif existing_text.strip() == rule_text:
            # Existing file is identical to standard suite rules without markers
            new_text = marked_block + "\n"
        else:
            # User content exists; append marked block
            new_text = existing_text.rstrip() + "\n\n" + marked_block + "\n"

        dest_rule_file.write_text(new_text, encoding="utf-8")

        action = "created" if prior_action == "created" else "merged"
        manifest_files[rel_path] = {
            "action": action,
            "sha256": compute_sha256(dest_rule_file),
            "original_content": original_content,
        }
    else:
        dest_rule_file.write_text(marked_block + "\n", encoding="utf-8")
        manifest_files[rel_path] = {
            "action": "created",
            "sha256": compute_sha256(dest_rule_file),
        }


def run_install(
    target_dir: Path,
    mode: str,
    repo_root: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """Execute installation and produce manifest."""
    target_dir = target_dir.resolve()
    
    if target_dir.name == "skills":
        dest_skills_dir = target_dir
        dest_root = target_dir.parent
    else:
        dest_skills_dir = target_dir / "skills"
        dest_root = target_dir

    if mode == "workspace" and dest_root.resolve() == repo_root.resolve():
        print("❌ Error: Refusing to install into the source repository root. Pass --target-dir <project_path>.")
        return 1

    if verbose:
        print(f"📦 Installing Antigravity Skills Suite:")
        print(f"   Mode: {mode}")
        print(f"   Root Destination: {dest_root}")
        print(f"   Skills Destination: {dest_skills_dir}")
        print(f"   Source Repo: {repo_root}")

    if dry_run:
        print(f"🔍 Dry-run enabled: Would install {len(SKILL_INVENTORY)} skills and runtime helpers into {dest_root} (no files written).")
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)
    dest_skills_dir.mkdir(parents=True, exist_ok=True)

    # Read existing manifest if present for idempotent preservation of original content
    manifest_path = dest_root / MANIFEST_FILENAME
    existing_manifest_files = {}
    if manifest_path.exists():
        try:
            old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing_manifest_files = old_manifest.get("files", {})
        except Exception:
            existing_manifest_files = {}

    manifest_files = {}

    # 1. Install explicit skills inventory
    installed_skills = []
    for skill_name in SKILL_INVENTORY:
        src_skill = repo_root / skill_name
        if src_skill.exists() and (src_skill / "SKILL.md").exists():
            copy_skill(
                skill_name,
                repo_root,
                dest_skills_dir,
                dest_root,
                manifest_files,
                verbose=verbose,
            )
            installed_skills.append(skill_name)
        elif verbose:
            print(f"⚠️  Skipping missing skill: {skill_name}")

    # 2. Install runtime helpers & shared output-policy reference
    for script_rel in RUNTIME_SCRIPTS:
        src_script = repo_root / script_rel
        dest_script = dest_root / script_rel
        copy_runtime_file(src_script, dest_script, dest_root, manifest_files, verbose=verbose)

    output_policy_src = repo_root / "references" / "output-policy.md"
    if output_policy_src.exists():
        dest_policy_ref = dest_skills_dir / "references" / "output-policy.md"
        copy_runtime_file(
            output_policy_src,
            dest_policy_ref,
            dest_root,
            manifest_files,
            verbose=verbose,
        )
        if dest_skills_dir != dest_root and dest_policy_ref.is_file():
            updated_text = dest_policy_ref.read_text(encoding="utf-8").replace(
                "(../suite-policy.json)", "(../../suite-policy.json)"
            )
            dest_policy_ref.write_text(updated_text, encoding="utf-8")
            rel_ref = dest_policy_ref.relative_to(dest_root).as_posix()
            if rel_ref in manifest_files:
                manifest_files[rel_ref]["sha256"] = compute_sha256(dest_policy_ref)

    # 3. Install suite policy
    for policy_file in POLICY_FILES:
        src_policy = repo_root / policy_file
        dest_policy = dest_root / policy_file
        copy_runtime_file(src_policy, dest_policy, dest_root, manifest_files, verbose=verbose)

    # 4. Safe merge hooks
    src_hooks = repo_root / ".agents" / "hooks.json"
    dest_hooks = dest_root / ".agents" / "hooks.json"
    safe_merge_hooks(
        src_hooks,
        dest_hooks,
        dest_root,
        manifest_files,
        existing_manifest_files,
        verbose=verbose,
    )

    # 5. Safe merge rules (AGENTS.md & GEMINI.md)
    for rule_file in RULE_FILES:
        src_rule = repo_root / rule_file
        dest_rule = dest_root / rule_file
        safe_merge_rules(
            src_rule,
            dest_rule,
            dest_root,
            manifest_files,
            existing_manifest_files,
            verbose=verbose,
        )

    # 5b. Prune obsolete files from previous manifest that are no longer part of suite
    for old_rel, old_info in existing_manifest_files.items():
        if old_rel not in manifest_files and old_info.get("action") == "created":
            old_file = dest_root / old_rel
            if old_file.exists():
                try:
                    old_file.unlink()
                    if verbose:
                        print(f"🗑️  Pruned obsolete file: {old_file}")
                except OSError:
                    pass
                # Clean up empty parent directories
                parent = old_file.parent
                while parent != dest_root and parent != dest_skills_dir and parent.exists():
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                            parent = parent.parent
                        else:
                            break
                    except OSError:
                        break

    # 6. Build and write manifest
    manifest_data = {
        "manifest_version": "1.0",
        "suite_version": "2.3.0",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "target_dir": str(target_dir),
        "workspace_root": str(dest_root),
        "skills_dir": str(dest_skills_dir),
        "installed_skills": installed_skills,
        "files": manifest_files,
    }

    manifest_json = json.dumps(manifest_data, indent=2) + "\n"
    manifest_path.write_text(manifest_json, encoding="utf-8")

    # If dest_skills_dir is distinct from dest_root, place secondary manifest copy
    if dest_skills_dir != dest_root and dest_skills_dir.exists():
        try:
            (dest_skills_dir / MANIFEST_FILENAME).write_text(manifest_json, encoding="utf-8")
        except OSError:
            pass

    print(f"✅ Successfully installed {len(installed_skills)} skills and {len(manifest_files)} components.")
    print(f"📄 Manifest written to: {manifest_path}")
    return 0


def run_uninstall(
    target_dir: Path | None,
    dry_run: bool = False,
    verbose: bool = False,
    specific_skills: list[str] | None = None,
) -> int:
    """Read manifest and cleanly remove installed files, restoring user configuration.
    If specific_skills is provided, only remove those skills from the destination."""
    candidates = []
    if target_dir:
        td = target_dir.resolve()
        if td.name == "skills":
            candidates.extend([
                td.parent / MANIFEST_FILENAME,
                td / MANIFEST_FILENAME,
            ])
        else:
            candidates.extend([
                td / MANIFEST_FILENAME,
                td / "skills" / MANIFEST_FILENAME,
                td.parent / MANIFEST_FILENAME,
            ])

    candidates.extend([
        Path.cwd() / MANIFEST_FILENAME,
        Path.cwd() / "skills" / MANIFEST_FILENAME,
        Path.home() / ".gemini" / "config" / MANIFEST_FILENAME,
        Path.home() / ".gemini" / "config" / "skills" / MANIFEST_FILENAME,
        Path.home() / ".gemini" / "antigravity" / MANIFEST_FILENAME,
        Path.home() / ".gemini" / "antigravity" / "skills" / MANIFEST_FILENAME,
    ])

    manifest_path = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            manifest_path = cand
            break

    if not manifest_path:
        print("❌ Error: No .skills-install-manifest.json found to uninstall from.")
        return 1

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Error reading manifest {manifest_path}: {e}")
        return 1

    dest_root = manifest_path.parent.resolve()
    if "workspace_root" in manifest_data:
        root_cand = Path(manifest_data["workspace_root"]).resolve()
        if root_cand.exists():
            dest_root = root_cand

    files_map = manifest_data.get("files", {})
    installed_skills = manifest_data.get("installed_skills", [])

    # If specific skills requested, filter files_map to only those belonging to the skills
    target_skill_names = set(specific_skills) if specific_skills else None
    if target_skill_names:
        matched_files = {}
        for rel_path, info in files_map.items():
            # Check if rel_path belongs to one of the specified skills
            # Patterns: skills/<skill>/... or <skill>/...
            parts = Path(rel_path).parts
            is_match = False
            if len(parts) >= 1 and parts[0] in target_skill_names:
                is_match = True
            elif len(parts) >= 2 and parts[0] == "skills" and parts[1] in target_skill_names:
                is_match = True

            if is_match:
                matched_files[rel_path] = info

        if not matched_files:
            print(f"⚠️  No installed files found matching requested skill(s): {', '.join(sorted(target_skill_names))}")
            return 0

        target_files_map = matched_files
        if verbose:
            print(f"🗑️  Removing {len(target_skill_names)} skill(s) from {dest_root}: {', '.join(sorted(target_skill_names))}...")
    else:
        target_files_map = files_map
        if verbose:
            print(f"🗑️  Uninstalling suite from {dest_root} using {manifest_path}...")

    if dry_run:
        print(f"🔍 Dry-run: Would remove {len(target_files_map)} tracked components.")
        return 0

    removed_files = 0
    restored_files = 0

    for rel_path, info in target_files_map.items():
        file_path = (dest_root / rel_path).resolve()
        
        # Path containment check: ensure no path traversal escape from dest_root
        if not file_path.is_relative_to(dest_root.resolve()):
            if verbose:
                print(f"⚠️  Skipping unsafe path traversal target: {file_path}")
            continue

        action = info.get("action")

        if action == "created":
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    removed_files += 1
                except OSError as e:
                    if verbose:
                        print(f"⚠️  Could not remove {file_path}: {e}")

                # Clean up empty parent directories up to dest_root
                parent = file_path.parent
                while parent != dest_root and parent.is_relative_to(dest_root):
                    try:
                        parent.rmdir()  # Fails cleanly if directory is not empty
                        parent = parent.parent
                    except OSError:
                        break

        elif action == "merged":
            if file_path.suffix == ".json" and "added_keys" in info and file_path.exists():
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        for key in info["added_keys"]:
                            data.pop(key, None)
                        file_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                        restored_files += 1
                        continue
                except Exception:
                    pass
            if file_path.exists():
                current_text = file_path.read_text(encoding="utf-8")
                if RULES_MARKER_START in current_text and RULES_MARKER_END in current_text:
                    pattern = re.compile(
                        rf"\n*{re.escape(RULES_MARKER_START)}[\s\S]*?{re.escape(RULES_MARKER_END)}\n*"
                    )
                    stripped = pattern.sub("\n", current_text).strip()
                    file_path.write_text((stripped + "\n") if stripped else "", encoding="utf-8")
                    restored_files += 1
                    continue
            if "original_content" in info:
                try:
                    file_path.write_text(info["original_content"], encoding="utf-8")
                    restored_files += 1
                except OSError as e:
                    if verbose:
                        print(f"⚠️  Could not restore {file_path}: {e}")

    # If partial uninstall, update manifest file instead of deleting it
    if target_skill_names:
        remaining_files = {k: v for k, v in files_map.items() if k not in target_files_map}
        remaining_skills = [s for s in installed_skills if s not in target_skill_names]
        manifest_data["files"] = remaining_files
        manifest_data["installed_skills"] = remaining_skills
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        skills_dir_str = manifest_data.get("skills_dir")
        if skills_dir_str:
            sec_manifest = Path(skills_dir_str) / MANIFEST_FILENAME
            if sec_manifest.exists() and sec_manifest != manifest_path:
                try:
                    sec_manifest.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")
                except OSError:
                    pass
        print(f"✅ Successfully removed {len(target_skill_names)} skill(s) ({', '.join(sorted(target_skill_names))}): removed {removed_files} files.")
        return 0

    # Remove secondary manifest copy if it exists
    skills_dir_str = manifest_data.get("skills_dir")
    if skills_dir_str:
        sec_manifest = Path(skills_dir_str) / MANIFEST_FILENAME
        if sec_manifest.exists() and sec_manifest != manifest_path:
            try:
                sec_manifest.unlink()
            except OSError:
                pass
        # Clean up skills_dir if empty
        try:
            Path(skills_dir_str).rmdir()
        except OSError:
            pass

    # Remove primary manifest
    try:
        manifest_path.unlink()
    except OSError:
        pass

    print(f"✅ Successfully uninstalled: removed {removed_files} files, restored {restored_files} merged configs.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Skills Suite — Installer and Manifest Manager"
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help="Target directory (defaults to ~/.gemini/config/skills or ~/.gemini/antigravity/skills in global mode, or current working directory in workspace mode)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--global",
        dest="is_global",
        action="store_true",
        help="Install globally for all Antigravity projects",
    )
    mode_group.add_argument(
        "--workspace",
        dest="is_workspace",
        action="store_true",
        help="Install locally in project workspace (default if not global)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall skills suite and restore original configurations using manifest",
    )
    parser.add_argument(
        "--remove",
        nargs="+",
        metavar="SKILL",
        help="Selectively remove/uninstall one or more specific skills by name (e.g. --remove idea-council infra-pilot)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to disk",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()
    repo_root = find_repo_root()

    # Determine default target directory
    if args.target_dir:
        target_dir = args.target_dir.resolve()
        if args.is_global:
            mode = "global"
        elif args.is_workspace:
            mode = "workspace"
        else:
            mode = "workspace"
    else:
        if args.is_global:
            mode = "global"
            cfg_skills = Path.home() / ".gemini" / "config" / "skills"
            agy_skills = Path.home() / ".gemini" / "antigravity" / "skills"
            if cfg_skills.exists():
                target_dir = cfg_skills
            elif agy_skills.exists():
                target_dir = agy_skills
            elif (Path.home() / ".gemini" / "config").exists():
                target_dir = cfg_skills
            else:
                target_dir = agy_skills
        else:
            mode = "workspace"
            target_dir = Path.cwd().resolve()

    if args.uninstall or args.remove:
        return run_uninstall(
            target_dir=target_dir if (args.is_global or args.target_dir) else args.target_dir,
            dry_run=args.dry_run,
            verbose=args.verbose,
            specific_skills=args.remove,
        )

    return run_install(
        target_dir=target_dir,
        mode=mode,
        repo_root=repo_root,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
