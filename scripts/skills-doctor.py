#!/usr/bin/env python3
"""
Antigravity Skills Suite — Environment and Runtime Health Doctor
Diagnoses host paths, Python version, runtime helper availability, hook configuration,
and optional tool capabilities with graceful degradation.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

# Critical runtime helpers that must be present for the suite to operate
REQUIRED_RUNTIME_HELPERS = [
    "guard_anti_retry.py",
    "validate-skills.py",
    "skills-doctor.py",
]

# Optional external tool binaries
OPTIONAL_TOOLS = ["pytest", "playwright", "git", "node"]

SKILL_INVENTORY = [
    "code-reviewer",
    "deep-debugger",
    "frontend-artisan",
    "idea-council",
    "plan-master",
    "playwright-cli",
    "create-architect",
    "qa-sentinel",
    "runtime-reliability",
    "schema-craft",
    "security-verifier",
    "ship-it",
    "infra-pilot",
    "docs-architect",
]


def check_python() -> dict:
    """Verify host Python version meets minimum >= 3.9 requirement."""
    vi = sys.version_info
    version_str = f"{vi.major}.{vi.minor}.{vi.micro}"
    is_sound = vi >= (3, 9)
    return {
        "status": "ok" if is_sound else "failed",
        "version": version_str,
        "required": ">= 3.9",
        "executable": sys.executable,
        "critical": True,
        "message": f"Python {version_str}" if is_sound else f"Python {version_str} < 3.9 (unsupported)",
    }


def check_host_paths(project_dir: Path) -> dict:
    """Verify host execution path integrity and platform."""
    exists = project_dir.exists() and project_dir.is_dir()
    path_env = os.environ.get("PATH", "")
    return {
        "project_dir": str(project_dir.resolve()),
        "project_dir_exists": exists,
        "has_path_env": bool(path_env),
        "platform": sys.platform,
        "is_windows": sys.platform == "win32",
        "status": "ok" if exists and path_env else "warning",
    }


def find_helper(helper_name: str, project_dir: Path) -> Path | None:
    """Find a runtime helper across standard project directories with cross-platform alternatives."""
    names_to_try = [helper_name]
    if helper_name == "exec-proxy.sh":
        names_to_try.extend(["exec_proxy.py", "exec-proxy.cmd", "exec-proxy.py"])
    elif helper_name == "verify-release-gate.sh":
        names_to_try.extend(["verify_release_gate.py", "verify-release-gate.cmd", "verify-release-gate.py"])

    script_dir = Path(__file__).resolve().parent
    for name in names_to_try:
        candidates = [
            project_dir / "scripts" / name,
            project_dir / name,
            project_dir / ".agents" / "scripts" / name,
        ]
        if project_dir == script_dir.parent:
            candidates.append(script_dir / name)

        for cand in candidates:
            if cand.exists() and cand.is_file():
                return cand
    return None


def check_runtime_helpers(project_dir: Path) -> dict:
    """Verify all 5 required runtime helpers exist and are accessible."""
    results = {}
    all_sound = True

    for helper in REQUIRED_RUNTIME_HELPERS:
        found_path = find_helper(helper, project_dir)
        if found_path:
            is_exec = os.access(found_path, os.X_OK) or found_path.suffix == ".py"
            results[helper] = {
                "available": True,
                "status": "ok",
                "path": str(found_path),
                "executable": is_exec,
                "critical": True,
            }
        else:
            all_sound = False
            results[helper] = {
                "available": False,
                "status": "missing",
                "path": None,
                "critical": True,
            }

    return {
        "all_present": all_sound,
        "status": "ok" if all_sound else "failed",
        "helpers": results,
    }


def check_hooks(project_dir: Path) -> dict:
    """Verify .agents/hooks.json exists, is valid JSON, and contains evidence-policy."""
    candidates = [
        project_dir / ".agents" / "hooks.json",
        project_dir / "hooks.json",
    ]

    hooks_path = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            hooks_path = cand
            break

    if not hooks_path:
        return {
            "status": "missing",
            "available": False,
            "path": None,
            "critical": True,
            "message": "Missing .agents/hooks.json configuration",
        }

    try:
        content = hooks_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as e:
        return {
            "status": "invalid_json",
            "available": True,
            "path": str(hooks_path),
            "critical": True,
            "message": f"Invalid JSON syntax in {hooks_path.name}: {e}",
        }

    has_evidence_policy = "evidence-policy" in data
    if has_evidence_policy:
        return {
            "status": "ok",
            "available": True,
            "path": str(hooks_path),
            "evidence_policy_configured": True,
            "critical": True,
            "message": "evidence-policy hook configured and active",
        }
    else:
        return {
            "status": "missing_evidence_policy",
            "available": True,
            "path": str(hooks_path),
            "evidence_policy_configured": False,
            "critical": True,
            "message": "hooks.json missing 'evidence-policy' release gate interception",
        }


def check_optional_tool(tool_name: str) -> dict:
    """
    Check availability of optional tools (pytest, playwright, git, node).
    Graceful degradation: missing optional tools report 'Optional: missing'
    without failing core health.
    """
    binary_path = shutil.which(tool_name)
    if not binary_path and tool_name == "playwright":
        binary_path = shutil.which("playwright-cli")

    version_str = None
    if binary_path:
        try:
            flag = "--version" if tool_name in {"git", "pytest", "playwright"} else "-v"
            out = subprocess.check_output(
                [binary_path, flag],
                stderr=subprocess.STDOUT,
                timeout=3,
                text=True,
            ).strip().splitlines()[0]
            version_str = out
        except Exception:
            version_str = "Available"
        return {
            "available": True,
            "status": "ok",
            "path": binary_path,
            "version": version_str,
            "message": version_str,
            "critical": False,
        }

    # Python module fallback for pytest and playwright
    if tool_name in {"pytest", "playwright"}:
        try:
            spec = importlib.util.find_spec(tool_name)
            if spec:
                return {
                    "available": True,
                    "status": "ok",
                    "path": f"python -m {tool_name}",
                    "version": "Importable python module",
                    "message": "Available via Python import",
                    "critical": False,
                }
        except Exception:
            pass

    return {
        "available": False,
        "status": "optional_missing",
        "path": None,
        "version": None,
        "message": "Optional: missing",
        "critical": False,
    }


def check_optional_tools() -> dict:
    """Inspect all optional tools."""
    results = {}
    for tool in OPTIONAL_TOOLS:
        results[tool] = check_optional_tool(tool)
    return results


def check_skills(project_dir: Path) -> dict:
    """Inspect presence of suite skills."""
    search_dirs = [
        project_dir / "skills",
        project_dir,
        project_dir / ".agents" / "skills",
        Path.home() / ".gemini" / "config" / "skills",
        Path.home() / ".gemini" / "antigravity" / "skills",
    ]

    found = set()
    detected_base = None

    for base in search_dirs:
        if base.exists() and base.is_dir():
            for skill in SKILL_INVENTORY:
                skill_file = base / skill / "SKILL.md"
                if skill_file.exists():
                    found.add(skill)
                    if not detected_base:
                        detected_base = base

    total = len(SKILL_INVENTORY)
    count = len(found)
    return {
        "total_skills": total,
        "found_count": count,
        "detected_base": str(detected_base) if detected_base else None,
        "missing_skills": sorted(list(set(SKILL_INVENTORY) - found)),
        "status": "ok" if count == total else ("partial" if count > 0 else "missing"),
    }


def diagnose_environment(project_dir: Path) -> dict:
    """Run full diagnostic suite and determine core health."""
    python_res = check_python()
    paths_res = check_host_paths(project_dir)
    helpers_res = check_runtime_helpers(project_dir)
    hooks_res = check_hooks(project_dir)
    optional_res = check_optional_tools()
    skills_res = check_skills(project_dir)

    core_sound = (
        python_res["status"] == "ok"
        and helpers_res["status"] == "ok"
        and hooks_res["status"] == "ok"
    )

    return {
        "status": "healthy" if core_sound else "unhealthy",
        "core_sound": core_sound,
        "python": python_res,
        "host_paths": paths_res,
        "runtime_helpers": helpers_res,
        "hooks": hooks_res,
        "optional_tools": optional_res,
        "skills": skills_res,
    }


def format_cli_report(diag: dict) -> str:
    """Format diagnostic results into a readable CLI report."""
    lines = []
    lines.append("🩺 Antigravity Skills Suite Doctor")
    lines.append("=" * 62)

    # Host & Python
    py = diag["python"]
    hp = diag["host_paths"]
    py_badge = "[✅ OK]" if py["status"] == "ok" else "[❌ FAIL]"
    lines.append("Host & Python:")
    platform_name = "Windows" if hp.get("is_windows") else ("macOS" if sys.platform == "darwin" else "Linux/POSIX")
    lines.append(f"  Operating System: {platform_name} ({sys.platform}) ".ljust(50, ".") + " [✅ OK]")
    lines.append(f"  Python Version: {py['version']} (>= 3.9) ".ljust(50, ".") + f" {py_badge}")
    proj_badge = "[✅ OK]" if hp["project_dir_exists"] else "[❌ FAIL]"
    lines.append(f"  Project Directory: {hp['project_dir']} ".ljust(50, ".") + f" {proj_badge}")
    lines.append("")

    # Runtime Helpers
    lines.append("Runtime Helpers:")
    for helper_name, info in diag["runtime_helpers"]["helpers"].items():
        badge = "[✅ OK]" if info["status"] == "ok" else "[❌ FAIL]"
        note = f"({info['path']})" if info["path"] else "(Missing)"
        lines.append(f"  {helper_name} ".ljust(50, ".") + f" {badge} {note}")
    lines.append("")

    # Hooks
    lines.append("Hook Configuration:")
    hooks = diag["hooks"]
    hook_badge = "[✅ OK]" if hooks["status"] == "ok" else "[❌ FAIL]"
    lines.append(f"  .agents/hooks.json ".ljust(50, ".") + f" {hook_badge} ({hooks['message']})")
    lines.append("")

    # Optional Tools
    lines.append("Optional Tool Capabilities:")
    for tool_name, info in diag["optional_tools"].items():
        if info["status"] == "ok":
            lines.append(f"  {tool_name} ".ljust(50, ".") + f" [✅ OK] ({info['message']})")
        else:
            lines.append(f"  {tool_name} ".ljust(50, ".") + f" [⚠️ Optional: missing]")
    lines.append("")

    # Skills Inventory
    skills = diag["skills"]
    sk_badge = "[✅ OK]" if skills["status"] == "ok" else "[⚠️ Incomplete]"
    lines.append("Skills Inventory:")
    lines.append(
        f"  Found {skills['found_count']}/{skills['total_skills']} suite skills ".ljust(50, ".")
        + f" {sk_badge}"
    )
    lines.append("=" * 62)

    if diag["core_sound"]:
        lines.append("Status: HEALTHY (Core health sound: all critical components verified)")
    else:
        lines.append("Status: UNHEALTHY (Core health failed: critical components missing)")

    return "\n".join(lines)


def heal_environment(project_dir: Path) -> list[str]:
    """
    Self-healing routine (WP-06 / HEAL-01):
    Repairs missing directories, restores missing hooks, copies missing runtime helpers
    from suite source root if available, and fixes executable permissions.
    Returns a list of repair actions performed.
    """
    actions = []
    source_root = Path(__file__).resolve().parent.parent

    # 1. Essential directories
    dirs_to_create = [
        project_dir / ".agents",
        project_dir / "scripts",
    ]
    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            try:
                rel = d.relative_to(project_dir)
            except ValueError:
                rel = d
            actions.append(f"Created directory: {rel}")

    # 2. Runtime Helpers restoration & permission repair
    source_scripts = source_root / "scripts"
    target_scripts = project_dir / "scripts"

    for helper in REQUIRED_RUNTIME_HELPERS:
        helper_path = find_helper(helper, project_dir)
        if not helper_path and source_scripts.exists():
            src_file = source_scripts / helper
            if src_file.exists():
                dst_file = target_scripts / helper
                shutil.copy2(src_file, dst_file)
                helper_path = dst_file
                actions.append(f"Restored runtime helper: scripts/{helper}")

        if helper_path and helper_path.exists():
            if sys.platform != "win32":
                try:
                    cur_mode = helper_path.stat().st_mode
                    if not (cur_mode & 0o111):
                        helper_path.chmod(cur_mode | 0o755)
                        actions.append(f"Added executable permission to: {helper_path.name}")
                except Exception:
                    pass

    # 3. Hooks configuration repair
    hooks_file = project_dir / ".agents" / "hooks.json"
    needs_hooks = False
    if not hooks_file.exists():
        needs_hooks = True
    else:
        try:
            content = json.loads(hooks_file.read_text(encoding="utf-8"))
            if "evidence-policy" not in content:
                needs_hooks = True
        except Exception:
            needs_hooks = True

    if needs_hooks:
        source_hooks = source_root / ".agents" / "hooks.json"
        if source_hooks.exists():
            shutil.copy2(source_hooks, hooks_file)
            actions.append("Restored .agents/hooks.json from suite template")
        else:
            python_bin = "python3" if shutil.which("python3") and sys.platform != "win32" else "python"
            hook_cmd = f"{python_bin} -c \"import os,runpy; p='scripts/guard_anti_retry.py'; runpy.run_path(p if os.path.exists(p) else '../'+p, run_name='__main__')\""
            default_hooks = {
                "evidence-policy": {
                    "PreToolUse": [
                        {
                            "matcher": "run_command",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_cmd,
                                    "timeout": 5
                                }
                            ]
                        }
                    ],
                    "PostToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_cmd,
                                    "timeout": 5
                                }
                            ]
                        }
                    ]
                }
            }
            hooks_file.write_text(json.dumps(default_hooks, indent=2), encoding="utf-8")
            actions.append("Created default .agents/hooks.json with evidence-policy")

    return actions


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Skills Suite — Environment and Runtime Health Doctor"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Target project directory to diagnose (defaults to current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON health report",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically repair missing directories, hooks, and permissions (self-healing)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()
    project_dir = args.project_dir.resolve()

    repairs_applied = []
    if args.fix:
        repairs_applied = heal_environment(project_dir)
        if not args.json:
            if repairs_applied:
                print("🛠️ Antigravity Doctor: Self-Healing Repairs Applied")
                print("=" * 62)
                for act in repairs_applied:
                    print(f"  [FIXED] {act}")
                print("=" * 62)
                print("")
            else:
                print("🛠️ Antigravity Doctor: Environment already intact, no repairs needed.\n")

    diag = diagnose_environment(project_dir)
    if args.fix:
        diag["repairs_applied"] = repairs_applied

    if args.json:
        print(json.dumps(diag, indent=2))
    else:
        print(format_cli_report(diag))

    return 0 if diag["core_sound"] else 1


if __name__ == "__main__":
    sys.exit(main())
