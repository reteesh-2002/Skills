#!/usr/bin/env python3
"""
Slice Guard — Mechanical Architectural Boundary and LOC Scanner.
Zero-dependency static analyzer enforcing Vertical Slice Architecture rules:
1. Cross-Slice Isolation: Slices must communicate ONLY via contracts or event bus;
   direct imports of sibling slice internals (e.g. '../other/service') are forbidden.
2. Sub-600 LOC Discipline: Implementation files (service, routes, handlers) must not
   exceed 300 LOC to keep LLM context footprint bounded.
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
    max_loc: int = 300,
    enforce_loc: bool = True,
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

                # 1. LOC check on non-test implementation files
                if enforce_loc and not is_test_file(file_path):
                    loc = count_lines_of_code(file_path)
                    if loc > max_loc:
                        violations.append({
                            "type": "loc_exceeded",
                            "severity": "WARNING",
                            "file": rel_file,
                            "line": 0,
                            "module": mod_name,
                            "message": f"File exceeds {max_loc} LOC ceiling ({loc} non-empty lines). Split logic into sub-handlers.",
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

    # Any CRITICAL violation causes failure
    has_critical = any(v.get("severity") == "CRITICAL" for v in violations)
    has_loc_errors = any(v.get("type") == "loc_exceeded" for v in violations)

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
        default=300,
        help="Maximum lines of code allowed per implementation file (default: 300)",
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
    )

    if args.json:
        print(json.dumps(findings, indent=2))
        sys.exit(0 if findings["status"] == "pass" else 1)

    # Human-readable output
    violations = findings["violations"]
    if not violations:
        if not args.quiet:
            mods = findings["modules_checked"]
            files = findings["files_checked"]
            print(f"✅ [slice-guard] All module boundaries and LOC limits respected.")
            print(f"   Checked {mods} vertical slices ({files} source files). Zero violations.")
        sys.exit(0)

    print(f"\n🚨 [slice-guard] Detected {len(violations)} architectural boundary violation(s):\n")
    for v in violations:
        sev = v.get("severity", "ERROR")
        loc_info = f":{v['line']}" if v['line'] > 0 else ""
        print(f"  [{sev}] {v['file']}{loc_info}")
        print(f"     └── {v['message']}")

    print(f"\n❌ Failure: Vertical slice boundary rules violated. Run failed with exit 1.\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
