#!/usr/bin/env python3
"""
Slice Guard — Mechanical Architectural Boundary and LOC Scanner.
Zero-dependency static analyzer enforcing Vertical Slice Architecture rules:
1. Cross-Slice Isolation: Slices must communicate ONLY via contracts or event bus;
   direct imports of sibling slice internals (e.g. '../other/service') are forbidden.
2. Context Boundedness & Cohesion: Implementation files should target ≤ 600 LOC to keep
   LLM context bounded. Highly cohesive modules (state machines, parsers, declarative
   schemas, auth boundaries) up to 1,200–1,500 LOC emit advisory warnings rather than hard
   failures unless --fail-on-loc is explicitly requested. Mechanical lasagna splitting
   into shallow *_helpers or *_utils is strictly discouraged.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Tuple

# Supported source file extensions
SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}

# Patterns for test files (exempt from strict LOC limits)
TEST_PATTERNS = [
    re.compile(r"\.test\.[a-zA-Z0-9]+$"),
    re.compile(r"\.spec\.[a-zA-Z0-9]+$"),
    re.compile(r"^test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r"/__tests__/"),
]

# Patterns for files exempt from LOC limits (tests, schemas, migrations, models)
LOC_EXEMPT_PATTERNS = [
    *TEST_PATTERNS,
    re.compile(r"schema\.[a-zA-Z0-9]+$"),
    re.compile(r"\.schema\.[a-zA-Z0-9]+$"),
    re.compile(r"models?\.[a-zA-Z0-9]+$"),
    re.compile(r"/migrations/"),
]

LOC_PRAGMA_RE = re.compile(r"""(?:@slice-guard-allow-loc|@allow-loc)""")

# Permitted public contract targets
ALLOWED_CONTRACT_NAMES = {"contract", "contract.ts", "contract.js", "contract.py", "types", "types.ts", "types.js"}

# Regex patterns for imports in JS/TS
JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?from\s+['"](?P<path>[^'"]+)['"]|"""
    r"""import\s*\(['"](?P<dyn_path>[^'"]+)['"]\)|"""
    r"""require\s*\(['"](?P<req_path>[^'"]+)['"]\)|"""
    r"""export\s+.*?from\s+['"](?P<exp_path>[^'"]+)['"])"""
)

# Regex patterns for imports in Python
PY_FROM_IMPORT_RE = re.compile(
    r"""^from\s+(?P<mod>\.+[a-zA-Z0-9_\.]+|[a-zA-Z0-9_\.]+)\s+import"""
)
PY_DIRECT_IMPORT_RE = re.compile(
    r"""^import\s+(?P<mod>[a-zA-Z0-9_\.]+)"""
)


def is_test_file(path: Path) -> bool:
    """Check if file is a test file based on naming convention."""
    path_str = str(path).replace("\\", "/")
    filename = path.name
    for pat in TEST_PATTERNS:
        if pat.search(filename) or pat.search(path_str):
            return True
    return False


def is_loc_exempt(file_path: Path) -> bool:
    """Check if file is exempt from LOC guidelines based on name or in-file pragma."""
    path_str = str(file_path).replace("\\", "/")
    filename = file_path.name
    for pat in LOC_EXEMPT_PATTERNS:
        if pat.search(filename) or pat.search(path_str):
            return True

    # Check first 15 lines for pragma
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i > 15:
                    break
                if LOC_PRAGMA_RE.search(line):
                    return True
    except Exception:
        pass

    return False


def find_modules_root(target_dir: Path) -> Optional[Path]:
    """Find the root directory containing vertical slice modules."""
    candidates = [
        target_dir / "src" / "modules",
        target_dir / "modules",
        target_dir / "app" / "modules",
        target_dir,
    ]
    for c in candidates:
        if c.is_dir():
            # Check if directory has at least one subfolder that looks like a module
            subdirs = [p for p in c.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))]
            if subdirs and c != target_dir:
                return c
            elif c == target_dir and c.name == "modules":
                return c
    return None


def count_lines_of_code(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f]
            return len([line for line in lines if line and not line.startswith(("#", "//", "/*", "*"))])
    except Exception:
        return 0


def analyze_js_import(import_path: str, current_module: str, all_modules: set) -> Optional[str]:
    """
    Check if a JS/TS import path targets sibling module internals.
    Returns error message if violation, None if compliant.
    """
    clean_path = import_path.strip().replace("\\", "/")
    
    # Check relative imports: e.g. ../other_module/service
    parts = clean_path.split("/")
    
    target_module = None
    subpath = ""

    if clean_path.startswith("../"):
        # e.g., ../billing/service -> parts = ['..', 'billing', 'service']
        if len(parts) >= 2 and parts[1] in all_modules:
            target_module = parts[1]
            subpath = "/".join(parts[2:]) if len(parts) > 2 else ""
        elif len(parts) >= 3 and parts[1] == "modules" and parts[2] in all_modules:
            # e.g., ../../modules/billing/service
            target_module = parts[2]
            subpath = "/".join(parts[3:]) if len(parts) > 3 else ""
    elif clean_path.startswith(("@/modules/", "~/modules/", "modules/")):
        # Path alias e.g. @/modules/billing/service
        mod_index = parts.index("modules") + 1
        if mod_index < len(parts) and parts[mod_index] in all_modules:
            target_module = parts[mod_index]
            subpath = "/".join(parts[mod_index + 1:]) if len(parts) > mod_index + 1 else ""

    if target_module and target_module != current_module:
        # It's a cross-slice import! Verify if it points to a contract
        stem = subpath.split(".")[0] if subpath else ""
        if not stem or stem in ALLOWED_CONTRACT_NAMES or stem.endswith("contract"):
            return None  # Allowed contract interface import
        return f"Illegal internal import from peer slice '{target_module}': '{clean_path}' (only contract imports allowed)"

    return None


def analyze_py_import(mod_name: str, current_module: str, all_modules: set) -> Optional[str]:
    """
    Check if a Python import targets sibling module internals.
    Returns error message if violation, None if compliant.
    """
    parts = mod_name.split(".")
    target_module = None
    subpath = ""

    # Relative imports like: from ..billing.service import x
    if mod_name.startswith(".."):
        clean_parts = [p for p in parts if p]
        if clean_parts and clean_parts[0] in all_modules:
            target_module = clean_parts[0]
            subpath = ".".join(clean_parts[1:])
    # Absolute package imports: from modules.billing.service import x
    elif "modules" in parts:
        idx = parts.index("modules") + 1
        if idx < len(parts) and parts[idx] in all_modules:
            target_module = parts[idx]
            subpath = ".".join(parts[idx + 1:])

    if target_module and target_module != current_module:
        if not subpath or subpath in ALLOWED_CONTRACT_NAMES or subpath.endswith("contract"):
            return None
        return f"Illegal internal import from peer slice '{target_module}': '{mod_name}' (only contract imports allowed)"

    return None


def scan_file_imports(file_path: Path, current_module: str, all_modules: set) -> List[Tuple[int, str]]:
    """Scan a source file for illegal cross-slice imports."""
    violations = []
    ext = file_path.suffix.lower()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith(("//", "/*", "#", "*")):
                    continue

                if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                    for match in JS_IMPORT_RE.finditer(line):
                        import_path = match.group("path") or match.group("dyn_path") or match.group("req_path") or match.group("exp_path")
                        if import_path:
                            err = analyze_js_import(import_path, current_module, all_modules)
                            if err:
                                violations.append((line_no, err))
                elif ext == ".py":
                    m_from = PY_FROM_IMPORT_RE.match(stripped)
                    if m_from:
                        err = analyze_py_import(m_from.group("mod"), current_module, all_modules)
                        if err:
                            violations.append((line_no, err))
                    else:
                        m_dir = PY_DIRECT_IMPORT_RE.match(stripped)
                        if m_dir:
                            err = analyze_py_import(m_dir.group("mod"), current_module, all_modules)
                            if err:
                                violations.append((line_no, err))
    except Exception as e:
        violations.append((0, f"Failed to read file: {e}"))

    return violations


def scan_slice_project(
    target_dir: Path,
    max_loc: int = 600,
    enforce_loc: bool = True,
    fail_on_loc: bool = False,
) -> Dict:
    """
    Main scanning routine. Returns a structured dictionary of findings.
    """
    modules_root = find_modules_root(target_dir)
    results = {
        "status": "pass",
        "target_dir": str(target_dir),
        "modules_root": str(modules_root) if modules_root else None,
        "modules_checked": 0,
        "files_checked": 0,
        "violations": [],
        "summary": {},
    }

    if not modules_root or not modules_root.is_dir():
        results["status"] = "pass"
        results["summary"] = {"message": "No vertical slice modules directory detected (skipped)"}
        return results

    # Identify all top-level module folders
    module_dirs = {
        p.name: p for p in modules_root.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    }
    all_modules = set(module_dirs.keys())
    results["modules_checked"] = len(all_modules)

    files_count = 0
    violations = []

    for mod_name, mod_dir in module_dirs.items():
        for root, _, files in os.walk(mod_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
                    continue

                files_count += 1
                rel_file = str(file_path.relative_to(target_dir))

                # 1. LOC check on non-exempt implementation files
                if enforce_loc and not is_loc_exempt(file_path):
                    loc = count_lines_of_code(file_path)
                    if loc > max_loc:
                        violations.append({
                            "type": "loc_exceeded",
                            "severity": "WARNING",
                            "file": rel_file,
                            "line": 0,
                            "module": mod_name,
                            "message": (
                                f"File exceeds {max_loc} LOC guideline ({loc} non-empty lines). "
                                f"Verify cyclomatic complexity (≤15) and domain cohesion. "
                                f"Avoid mechanical helper splitting (*_utils, *_helpers) that fragments atomic transactions."
                            ),
                            "loc": loc,
                            "max_loc": max_loc,
                        })

                # 2. Cross-slice import check
                import_violations = scan_file_imports(file_path, mod_name, all_modules)
                for line_no, err_msg in import_violations:
                    violations.append({
                        "type": "illegal_cross_slice_import",
                        "severity": "CRITICAL",
                        "file": rel_file,
                        "line": line_no,
                        "module": mod_name,
                        "message": err_msg,
                    })

    results["files_checked"] = files_count
    results["violations"] = violations

    # Any CRITICAL violation causes failure; LOC warnings only fail if fail_on_loc is True
    has_critical = any(v.get("severity") == "CRITICAL" for v in violations)
    has_loc_errors = fail_on_loc and any(v.get("type") == "loc_exceeded" for v in violations)

    if has_critical or has_loc_errors:
        results["status"] = "fail"
    else:
        results["status"] = "pass"

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Slice Guard — Vertical Slice Architecture Boundary and LOC Linter"
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Path to project or source root containing modules/ (default: current directory)",
    )
    parser.add_argument(
        "--max-loc",
        type=int,
        default=600,
        help="Maximum lines of code allowed per implementation file before advisory warning (default: 600)",
    )
    parser.add_argument(
        "--fail-on-loc",
        action="store_true",
        help="Treat LOC ceiling exceedance as a hard build failure rather than an advisory warning",
    )
    parser.add_argument(
        "--no-loc-check",
        action="store_true",
        help="Disable lines of code ceiling check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON for tool receipts",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors",
    )

    args = parser.parse_args()
    target_path = Path(args.target_dir).resolve()

    if not target_path.exists():
        if args.json:
            print(json.dumps({"status": "error", "message": f"Path not found: {target_path}"}))
        else:
            print(f"❌ Error: Path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    findings = scan_slice_project(
        target_dir=target_path,
        max_loc=args.max_loc,
        enforce_loc=not args.no_loc_check,
        fail_on_loc=args.fail_on_loc,
    )

    if args.json:
        print(json.dumps(findings, indent=2))
        sys.exit(0 if findings["status"] == "pass" else 1)

    # Human-readable output
    critical_violations = [v for v in findings["violations"] if v.get("severity") == "CRITICAL"]
    loc_warnings = [v for v in findings["violations"] if v.get("type") == "loc_exceeded"]

    if not findings["violations"]:
        if not args.quiet:
            mods = findings["modules_checked"]
            files = findings["files_checked"]
            print(f"✅ [slice-guard] All module boundaries and LOC limits respected.")
            print(f"   Checked {mods} vertical slices ({files} source files). Zero violations.")
        sys.exit(0)

    if critical_violations:
        print(f"\n🚨 [slice-guard] Detected {len(critical_violations)} architectural boundary violation(s):\n")
        for v in critical_violations:
            loc_info = f":{v['line']}" if v['line'] > 0 else ""
            print(f"  [CRITICAL] {v['file']}{loc_info}")
            print(f"     └── {v['message']}")

    if loc_warnings:
        prefix = "🚨" if args.fail_on_loc else "⚠️"
        status_label = "ERROR" if args.fail_on_loc else "WARNING"
        print(f"\n{prefix} [slice-guard] Detected {len(loc_warnings)} file(s) exceeding {args.max_loc} LOC guideline:\n")
        for v in loc_warnings:
            print(f"  [{status_label}] {v['file']}")
            print(f"     └── {v['message']}")

    if findings["status"] == "fail":
        print(f"\n❌ Failure: Vertical slice rules violated. Run failed with exit 1.\n")
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"\n✅ [slice-guard] Module boundaries clean. LOC advisories emitted without failure.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
