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
import ast
import json
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

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

# Regex for mechanical helper anti-pattern in slice directories (The Lasagna Blacklist)
MECHANICAL_HELPER_RE = re.compile(
    r"""^(?:.*[_-](?:helpers?|utils?|substate|sub_state|part[0-9]+|ops?|tools?|handlers?|delegates?|common|misc)\.[a-zA-Z0-9]+$|"""
    r""".*(?:Helpers?|Utils?|SubState|Ops?|Tools?|Handlers?|Delegates?|Common|Misc)\.[a-zA-Z0-9]+$)""",
    re.IGNORECASE
)

# Ubiquitous runtime, platform, and observability dependencies exempt from fan-out count
INFRASTRUCTURE_FAN_OUT_WHITELIST = {
    # Core React / Web runtime
    "react", "react-dom", "react/jsx-runtime", "next", "vue", "svelte",
    # Validation & Typing
    "zod", "pydantic", "typing", "typing_extensions", "types",
    # Logging, Observability & Telemetry
    "pino", "winston", "bunyan", "sentry", "@sentry/node", "@sentry/react",
    "prom-client", "@opentelemetry/api", "@opentelemetry/sdk-node",
    # Styling & UI Primitives
    "clsx", "tailwind-merge", "class-variance-authority", "lucide-react",
    # Common database drivers / clients
    "pg", "postgres", "redis", "ioredis", "prisma", "@prisma/client", "sqlite3",
    # Core system & Python stdlib
    "os", "sys", "re", "json", "pathlib", "math", "time", "datetime",
    "collections", "functools", "itertools", "dataclasses",
    "abc", "contextlib", "logging", "asyncio", "unittest",
}


def is_whitelisted_fan_out_dependency(target: str) -> bool:
    """Check if imported package is ubiquitous platform/framework infrastructure."""
    t = target.lower()
    if t in INFRASTRUCTURE_FAN_OUT_WHITELIST:
        return True
    if t.startswith(("@opentelemetry/", "react/", "@types/", "@sentry/")):
        return True
    return False


# Regex for JS/TS function boundaries & branching tokens
JS_FUNC_START_RE = re.compile(
    r"""(?:(?:async\s+)?function\s+(?P<f1>[a-zA-Z0-9_$]+)|"""
    r"""(?:const|let|var)\s+(?P<f2>[a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{|"""
    r"""(?P<f3>[a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{)"""
)
JS_BRANCH_TOKENS_RE = re.compile(
    r"""(\bif\b|\belse\s+if\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b|&&|\|\||\?\?|\?[^:\n\r]+:)"""
)

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


def is_mechanical_helper_file(file_path: Path) -> bool:
    """Detect if file matches lasagna helper naming conventions (*_helpers, *_utils, etc.)."""
    return bool(MECHANICAL_HELPER_RE.match(file_path.name))


def analyze_cyclomatic_complexity(file_path: Path) -> List[Tuple[str, int, int]]:
    """
    Computes cyclomatic complexity per function for Python and JS/TS.
    Returns list of (function_name, line_number, complexity).
    """
    ext = file_path.suffix.lower()
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    if ext == ".py":
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1
                for n in ast.walk(node):
                    if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.Assert)):
                        complexity += 1
                    elif isinstance(n, ast.BoolOp):
                        complexity += len(n.values) - 1
                    elif sys.version_info >= (3, 10) and isinstance(n, getattr(ast, "Match", ())):
                        complexity += len(getattr(n, "cases", []))
                results.append((node.name, node.lineno, complexity))
        return results

    elif ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        lines = content.splitlines()
        results = []
        current_func = None
        func_line = 0
        brace_depth = 0
        func_brace_depth = 0
        func_complexity = 1

        for idx, line in enumerate(lines, 1):
            stripped = line.split("//")[0].strip()
            if not current_func:
                m = JS_FUNC_START_RE.search(stripped)
                if m and "{" in stripped:
                    current_func = m.group("f1") or m.group("f2") or m.group("f3") or f"anonymous_L{idx}"
                    func_line = idx
                    func_brace_depth = brace_depth
                    func_complexity = 1

            if current_func:
                matches = JS_BRANCH_TOKENS_RE.findall(stripped)
                func_complexity += len(matches)

            brace_depth += stripped.count("{") - stripped.count("}")

            if current_func and brace_depth <= func_brace_depth:
                results.append((current_func, func_line, func_complexity))
                current_func = None

        return results

    return []


def calculate_module_fan_out(file_path: Path) -> Tuple[int, List[str]]:
    """
    Calculate module fan-out: number of unique external packages or peer slices imported.
    Excludes internal relative imports within the same module slice (e.g. ./types, ./contract).
    """
    ext = file_path.suffix.lower()
    targets: Set[str] = set()
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return 0, []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "/*", "#", "*")):
            continue

        if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            for match in JS_IMPORT_RE.finditer(line):
                p = match.group("path") or match.group("dyn_path") or match.group("req_path") or match.group("exp_path")
                if not p or p.startswith("./"):
                    continue
                if p.startswith(("../", "@/modules/", "~/modules/")):
                    clean = p.replace("@/", "").replace("~/", "")
                    parts = [x for x in clean.split("/") if x and x != ".."]
                    mod_target = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
                    if not is_whitelisted_fan_out_dependency(mod_target):
                        targets.add(mod_target)
                else:
                    parts = p.split("/")
                    pkg = parts[0] if not p.startswith("@") else "/".join(parts[:2])
                    if not is_whitelisted_fan_out_dependency(pkg):
                        targets.add(pkg)

        elif ext == ".py":
            m_from = PY_FROM_IMPORT_RE.match(stripped)
            if m_from:
                mod = m_from.group("mod")
                if mod.startswith(".") and not mod.startswith(".."):
                    continue
                if mod.startswith(".."):
                    clean = mod.lstrip(".")
                    target_pkg = clean.split(".")[0]
                else:
                    target_pkg = mod.split(".")[0]
                if not is_whitelisted_fan_out_dependency(target_pkg):
                    targets.add(target_pkg)
            else:
                m_dir = PY_DIRECT_IMPORT_RE.match(stripped)
                if m_dir:
                    target_pkg = m_dir.group("mod").split(".")[0]
                    if not is_whitelisted_fan_out_dependency(target_pkg):
                        targets.add(target_pkg)

    return len(targets), sorted(list(targets))


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
    max_cohesive_loc: int = 1500,
    max_cyclomatic: int = 15,
    max_total_cyclomatic: int = 50,
    max_fan_out: int = 7,
    enforce_loc: bool = True,
    fail_on_loc: bool = False,
    fail_on_complexity: bool = False,
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
        "compliant_enclosures": [],
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
    compliant_enclosures = []

    for mod_name, mod_dir in module_dirs.items():
        for root, _, files in os.walk(mod_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
                    continue

                files_count += 1
                rel_file = str(file_path.relative_to(target_dir))

                # 1. Mechanical helper anti-pattern check (Semantic Enclosure)
                if is_mechanical_helper_file(file_path):
                    violations.append({
                        "type": "mechanical_helper_detected",
                        "severity": "WARNING",
                        "file": rel_file,
                        "line": 0,
                        "module": mod_name,
                        "message": (
                            f"Mechanical helper file '{file_path.name}' detected. "
                            f"Violates Semantic Enclosure policy. Colocate atomic domain logic within the primary service "
                            f"or extract a formal domain slice; avoid shallow lasagna helpers (*_helpers, *_utils, *_ops)."
                        ),
                    })

                # 2. Complexity & Fan-Out analysis (Semantic Enclosure invariants)
                max_func_complexity = 0
                total_file_complexity = 0
                worst_func = ""
                worst_func_line = 0
                fan_out = 0
                targets: List[str] = []

                if not is_test_file(file_path):
                    funcs = analyze_cyclomatic_complexity(file_path)
                    total_file_complexity = sum(comp for _, _, comp in funcs)

                    for fname, fline, comp in funcs:
                        if comp > max_func_complexity:
                            max_func_complexity = comp
                            worst_func = fname
                            worst_func_line = fline
                        if comp > max_cyclomatic:
                            violations.append({
                                "type": "high_cyclomatic_complexity",
                                "severity": "WARNING",
                                "file": rel_file,
                                "line": fline,
                                "module": mod_name,
                                "message": (
                                    f"Function '{fname}' has cyclomatic complexity of {comp} (exceeds limit of {max_cyclomatic}). "
                                    f"Extract pure calculations or simplify branching logic."
                                ),
                                "complexity": comp,
                                "max_cyclomatic": max_cyclomatic,
                                "function": fname,
                            })

                    if total_file_complexity > max_total_cyclomatic:
                        violations.append({
                            "type": "high_total_complexity",
                            "severity": "WARNING",
                            "file": rel_file,
                            "line": 0,
                            "module": mod_name,
                            "message": (
                                f"Total file cyclomatic complexity of {total_file_complexity} exceeds ceiling of {max_total_cyclomatic} "
                                f"across {len(funcs)} functions. God-Slice hazard. Decompose slice into distinct capabilities."
                            ),
                            "total_complexity": total_file_complexity,
                            "max_total_cyclomatic": max_total_cyclomatic,
                        })

                    fan_out, targets = calculate_module_fan_out(file_path)
                    if fan_out > max_fan_out:
                        violations.append({
                            "type": "high_fan_out",
                            "severity": "WARNING",
                            "file": rel_file,
                            "line": 0,
                            "module": mod_name,
                            "message": (
                                f"Module fan-out of {fan_out} exceeds limit of {max_fan_out} (imports: {', '.join(targets[:5])}{'...' if len(targets) > 5 else ''}). "
                                f"High coupling hazard (God Object smell). Decouple via event bus or domain interfaces."
                            ),
                            "fan_out": fan_out,
                            "max_fan_out": max_fan_out,
                        })

                # 3. LOC check under Semantic Enclosure
                if enforce_loc and not is_loc_exempt(file_path):
                    loc = count_lines_of_code(file_path)
                    if loc > max_cohesive_loc:
                        violations.append({
                            "type": "loc_exceeded",
                            "severity": "WARNING",
                            "file": rel_file,
                            "line": 0,
                            "module": mod_name,
                            "message": (
                                f"File exceeds maximum cohesive ceiling of {max_cohesive_loc} LOC ({loc} non-empty lines). "
                                f"Decompose into distinct domain sub-slices."
                            ),
                            "loc": loc,
                            "max_loc": max_cohesive_loc,
                        })
                    elif loc > max_loc:
                        is_uncohesive = (
                            max_func_complexity > max_cyclomatic
                            or fan_out > max_fan_out
                            or total_file_complexity > max_total_cyclomatic
                        )
                        if is_uncohesive:
                            violations.append({
                                "type": "loc_exceeded",
                                "severity": "WARNING",
                                "file": rel_file,
                                "line": worst_func_line,
                                "module": mod_name,
                                "message": (
                                    f"File has {loc} LOC and violates Semantic Enclosure complexity bounds "
                                    f"(worst cyclomatic complexity: {max_func_complexity}/{max_cyclomatic}, "
                                    f"total complexity: {total_file_complexity}/{max_total_cyclomatic}, "
                                    f"fan-out: {fan_out}/{max_fan_out}). "
                                    f"Decompose uncohesive logic or extract pure calculation functions."
                                ),
                                "loc": loc,
                                "max_loc": max_loc,
                                "complexity": max_func_complexity,
                                "total_complexity": total_file_complexity,
                                "fan_out": fan_out,
                            })
                        else:
                            # Compliant Semantic Enclosure: render clean green [PASS], do not scold with warnings!
                            compliant_enclosures.append({
                                "file": rel_file,
                                "loc": loc,
                                "max_complexity": max_func_complexity,
                                "total_complexity": total_file_complexity,
                                "fan_out": fan_out,
                            })

                # 4. Cross-slice import check
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
    results["compliant_enclosures"] = compliant_enclosures

    # Any CRITICAL violation causes failure; LOC/complexity warnings only fail if explicitly requested
    has_critical = any(v.get("severity") == "CRITICAL" for v in violations)
    has_loc_errors = fail_on_loc and any(v.get("type") == "loc_exceeded" for v in violations)
    has_complexity_errors = fail_on_complexity and any(
        v.get("type") in ("high_cyclomatic_complexity", "high_total_complexity", "high_fan_out", "mechanical_helper_detected")
        for v in violations
    )

    if has_critical or has_loc_errors or has_complexity_errors:
        results["status"] = "fail"
    else:
        results["status"] = "pass"

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Slice Guard — Vertical Slice Architecture Boundary, Complexity & LOC Scanner"
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
        help="Target LOC guideline per implementation file (default: 600)",
    )
    parser.add_argument(
        "--max-cohesive-loc",
        type=int,
        default=1500,
        help="Maximum LOC ceiling for cohesive modules (default: 1500)",
    )
    parser.add_argument(
        "--max-cyclomatic",
        type=int,
        default=15,
        help="Maximum cyclomatic complexity per function (default: 15)",
    )
    parser.add_argument(
        "--max-total-cyclomatic",
        type=int,
        default=50,
        help="Maximum aggregate cyclomatic complexity per file (default: 50)",
    )
    parser.add_argument(
        "--max-fan-out",
        type=int,
        default=7,
        help="Maximum external module imports per file (default: 7)",
    )
    parser.add_argument(
        "--fail-on-loc",
        action="store_true",
        help="Treat LOC guideline exceedance as a hard build failure rather than an advisory warning",
    )
    parser.add_argument(
        "--fail-on-complexity",
        action="store_true",
        help="Treat cyclomatic complexity (>15) and fan-out (>7) violations as hard build failures",
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
        max_cohesive_loc=args.max_cohesive_loc,
        max_cyclomatic=args.max_cyclomatic,
        max_total_cyclomatic=args.max_total_cyclomatic,
        max_fan_out=args.max_fan_out,
        enforce_loc=not args.no_loc_check,
        fail_on_loc=args.fail_on_loc,
        fail_on_complexity=args.fail_on_complexity,
    )

    if args.json:
        print(json.dumps(findings, indent=2))
        sys.exit(0 if findings["status"] == "pass" else 1)

    # Human-readable output
    critical_violations = [v for v in findings["violations"] if v.get("severity") == "CRITICAL"]
    complexity_warnings = [
        v for v in findings["violations"]
        if v.get("type") in ("high_cyclomatic_complexity", "high_total_complexity", "high_fan_out")
    ]
    helper_warnings = [v for v in findings["violations"] if v.get("type") == "mechanical_helper_detected"]
    loc_warnings = [v for v in findings["violations"] if v.get("type") == "loc_exceeded"]

    if findings.get("compliant_enclosures") and not args.quiet:
        print(f"\n📦 [slice-guard] Verified {len(findings['compliant_enclosures'])} cohesive module(s) under Semantic Enclosure:\n")
        for ce in findings["compliant_enclosures"]:
            print(f"  ✅ [PASS: Semantic Enclosure] {ce['file']} ({ce['loc']} LOC, max CC: {ce['max_complexity']}, total CC: {ce['total_complexity']}, fan-out: {ce['fan_out']})")

    if not findings["violations"]:
        if not args.quiet:
            mods = findings["modules_checked"]
            files = findings["files_checked"]
            print(f"\n✅ [slice-guard] All module boundaries, complexity limits, and LOC guidelines respected.")
            print(f"   Checked {mods} vertical slices ({files} source files). Zero violations.")
        sys.exit(0)

    if critical_violations:
        print(f"\n🚨 [slice-guard] Detected {len(critical_violations)} architectural boundary violation(s):\n")
        for v in critical_violations:
            loc_info = f":{v['line']}" if v['line'] > 0 else ""
            print(f"  [CRITICAL] {v['file']}{loc_info}")
            print(f"     └── {v['message']}")

    if helper_warnings:
        prefix = "🚨" if args.fail_on_complexity else "⚠️"
        print(f"\n{prefix} [slice-guard] Detected {len(helper_warnings)} mechanical helper file(s) (Semantic Enclosure violation):\n")
        for v in helper_warnings:
            print(f"  [LASAGNA HELPER] {v['file']}")
            print(f"     └── {v['message']}")

    if complexity_warnings:
        prefix = "🚨" if args.fail_on_complexity else "⚠️"
        print(f"\n{prefix} [slice-guard] Detected {len(complexity_warnings)} complexity & coupling violation(s):\n")
        for v in complexity_warnings:
            loc_info = f":{v['line']}" if v['line'] > 0 else ""
            print(f"  [COMPLEXITY] {v['file']}{loc_info}")
            print(f"     └── {v['message']}")

    if loc_warnings:
        prefix = "🚨" if args.fail_on_loc else "⚠️"
        status_label = "ERROR" if args.fail_on_loc else "WARNING"
        print(f"\n{prefix} [slice-guard] Detected {len(loc_warnings)} file(s) exceeding LOC guidelines:\n")
        for v in loc_warnings:
            print(f"  [{status_label}] {v['file']}")
            print(f"     └── {v['message']}")

    if findings["status"] == "fail":
        print(f"\n❌ Failure: Vertical slice rules violated. Run failed with exit 1.\n")
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"\n✅ [slice-guard] Module boundaries clean. Complexity/LOC advisories emitted without failure.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
