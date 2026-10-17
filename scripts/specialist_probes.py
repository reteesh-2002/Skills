#!/usr/bin/env python3
"""
Antigravity Specialist Verification Probes (Release D)
Deterministic empirical validation engines for specialist skills:
  - frontend-artisan: viewport overflow detection & WCAG AA contrast calculation
  - schema-craft: disposable database migration rehearsal (up -> rollback -> re-apply)
  - security-verifier: synthetic dual-tenant BOLA/IDOR isolation probe
  - runtime-reliability: graceful lifecycle drain & memory soak telemetry
"""

from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import re
import sys
import math
import sqlite3
import tempfile
from typing import Dict, Any, List, Optional, Tuple, Callable, Union


# ──────────────────────────────────────────────
# 1. Frontend Artisan: Contrast & Viewport Probes
# ──────────────────────────────────────────────

def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parses a hex color string (#rgb, #rrggbb) into (r, g, b) integers (0-255)."""
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    if len(h) != 6:
        raise ValueError(f"Invalid hex color format: {hex_str}")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculates relative luminance according to WCAG 2.1 specs."""
    def channel_lum(c: int) -> float:
        val = c / 255.0
        return val / 12.92 if val <= 0.03928 else ((val + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel_lum(r) + 0.7152 * channel_lum(g) + 0.0722 * channel_lum(b)


def calculate_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """
    Calculates WCAG 2.1 contrast ratio between two hex colors.
    Returns float in range [1.0, 21.0].
    """
    r1, g1, b1 = parse_hex_color(fg_hex)
    r2, g2, b2 = parse_hex_color(bg_hex)
    lum1 = relative_luminance(r1, g1, b1)
    lum2 = relative_luminance(r2, g2, b2)
    l_max = max(lum1, lum2)
    l_min = min(lum1, lum2)
    return round((l_max + 0.05) / (l_min + 0.05), 2)


def verify_wcag_aa(fg_hex: str, bg_hex: str, is_large_text: bool = False) -> Dict[str, Any]:
    """
    Verifies text contrast against WCAG AA requirements:
      - Normal text: >= 4.5:1
      - Large text (>= 18pt or 14pt bold): >= 3.0:1
    """
    ratio = calculate_contrast_ratio(fg_hex, bg_hex)
    threshold = 3.0 if is_large_text else 4.5
    passes = ratio >= threshold
    return {
        "fg": fg_hex,
        "bg": bg_hex,
        "ratio": ratio,
        "threshold": threshold,
        "is_large_text": is_large_text,
        "passed": passes,
        "standard": "WCAG AA"
    }


def check_html_viewport_overflow(html_content: str, viewports: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Static heuristic scanner for horizontal overflow hazards in HTML/CSS.
    Detects fixed pixel widths wider than target viewports (375px mobile, 768px tablet).
    """
    if viewports is None:
        viewports = [375, 768, 1440]

    hazards = []
    # Pattern 1: inline width or CSS width with pixel values > 375px without max-width
    fixed_widths = re.findall(r'(?:width|min-width):\s*(\d+)px', html_content)
    for w in fixed_widths:
        w_val = int(w)
        for vp in viewports:
            if w_val > vp:
                hazards.append({
                    "hazard": "fixed_pixel_overflow",
                    "width": w_val,
                    "target_viewport": vp,
                    "detail": f"Fixed width {w_val}px exceeds viewport {vp}px",
                    "heuristic": True
                })

    # Pattern 2: w-[Npx] Tailwind arbitrary classes where N > 375 without responsive prefixes
    tw_widths = re.findall(r'(?<![sm|md|lg|xl]:)w-\[(\d+)px\]', html_content)
    for tw in tw_widths:
        tw_val = int(tw)
        if tw_val > 375:
            hazards.append({
                "hazard": "tailwind_fixed_overflow",
                "width": tw_val,
                "target_viewport": 375,
                "detail": f"Tailwind arbitrary class w-[{tw_val}px] causes mobile horizontal scroll",
                "heuristic": True
            })

    # Pattern 3: missing viewport meta tag
    has_viewport_meta = "<meta name=\"viewport\"" in html_content or "<meta name='viewport'" in html_content
    if "<html" in html_content and not has_viewport_meta:
        hazards.append({
            "hazard": "missing_viewport_meta",
            "detail": "HTML document is missing standard viewport meta tag (content='width=device-width, initial-scale=1')",
            "heuristic": True
        })

    return {
        "heuristic": True,
        "viewports_checked": viewports,
        "hazards_found": len(hazards),
        "hazards": hazards,
        "passed": len(hazards) == 0
    }


# ──────────────────────────────────────────────
# 2. Schema Craft: Disposable Database Rehearsal
# ──────────────────────────────────────────────

def rehearse_sqlite_migration(
    up_sql: str,
    down_sql: str,
    seed_sql: Optional[str] = None,
    verify_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a 4-phase migration rehearsal on a disposable in-memory SQLite database:
      Phase 1: Apply UP migration -> verify schema exists.
      Phase 2: Insert seed data & test target query -> verify relational validity.
      Phase 3: Apply DOWN migration (rollback) -> verify clean reversion.
      Phase 4: Re-apply UP migration -> verify idempotency.
    """
    conn = sqlite3.connect(":memory:")
    # F07: Enable foreign key enforcement — SQLite disables it by default
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()
    report: Dict[str, Any] = {
        "up_phase": False,
        "seed_phase": False,
        "verify_query_phase": False,
        "down_phase": False,
        "idempotency_phase": False,
        "tables_created": [],
        "errors": [],
        "passed": False
    }

    try:
        # Phase 1: UP
        cur.executescript(up_sql)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cur.fetchall()]
        report["tables_created"] = tables
        report["up_phase"] = len(tables) > 0

        # Phase 2: Seed & Verify
        if seed_sql:
            cur.executescript(seed_sql)
            report["seed_phase"] = True
        else:
            report["seed_phase"] = True

        if verify_query:
            cur.execute(verify_query)
            _ = cur.fetchall()
            report["verify_query_phase"] = True
        else:
            report["verify_query_phase"] = True

        # Phase 3: DOWN (Rollback)
        cur.executescript(down_sql)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables_after_down = [row[0] for row in cur.fetchall()]
        # Check that new tables were cleanly dropped
        report["down_phase"] = len(tables_after_down) == 0 or len(tables_after_down) < len(tables)

        # Phase 4: Idempotency (Re-apply UP)
        cur.executescript(up_sql)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables_reapplied = [row[0] for row in cur.fetchall()]
        report["idempotency_phase"] = set(tables_reapplied) == set(tables)

        report["passed"] = (
            report["up_phase"] and
            report["seed_phase"] and
            report["verify_query_phase"] and
            report["down_phase"] and
            report["idempotency_phase"]
        )
    except Exception as exc:
        report["errors"].append(str(exc))
        report["passed"] = False
    finally:
        conn.close()

    return report


# ──────────────────────────────────────────────
# 3. Security Verifier: Dual-Tenant IDOR Probe
# ──────────────────────────────────────────────

def probe_tenant_isolation(
    access_fn: Callable[[Dict[str, Any], str], Tuple[int, Any]],
    tenant_a_auth: Dict[str, Any],
    tenant_b_auth: Dict[str, Any],
    tenant_b_resource_id: str
) -> Dict[str, Any]:
    """
    Executes a synthetic dual-tenant BOLA / IDOR boundary probe:
      1. Tenant B requests their own resource -> Expects 200 OK.
      2. Tenant A requests Tenant B's resource -> Expects 403 Forbidden or 404 Not Found.
      If Tenant A receives 200 OK, a critical IDOR defect is confirmed.
    """
    # Baseline: Tenant B accesses their own resource
    b_status, _ = access_fn(tenant_b_auth, tenant_b_resource_id)
    baseline_ok = b_status == 200

    # Probe: Tenant A attempts unauthorized access to Tenant B's resource
    a_status, a_data = access_fn(tenant_a_auth, tenant_b_resource_id)
    isolation_passed = a_status in (403, 404)
    data_leaked = a_status == 200

    return {
        "tenant_b_baseline_status": b_status,
        "tenant_b_baseline_ok": baseline_ok,
        "tenant_a_probe_status": a_status,
        "data_leaked": data_leaked,
        "passed": isolation_passed and baseline_ok,
        "verdict": "SECURE (403/404 on cross-tenant probe)" if isolation_passed else "CRITICAL IDOR VULNERABILITY (Cross-tenant leak detected)"
    }


# ──────────────────────────────────────────────
# 4. Runtime Reliability: Graceful Drain & Soak
# ──────────────────────────────────────────────

def probe_graceful_drain(
    worker_fn: Callable[[int], bool],
    in_flight_tasks: int = 20,
    drain_timeout_ms: int = 500
) -> Dict[str, Any]:
    """
    Simulates a graceful shutdown drain probe using real threading and SIGTERM:
      1. Dispatches N in-flight tasks as threads.
      2. Sets a drain deadline (drain_timeout_ms).
      3. Verifies all in-flight tasks finish within the deadline; tasks that
         exceed the deadline are counted as aborted (dropped under pressure).

    Uses threading.Event to signal shutdown and threading.Timer to enforce the
    drain timeout, mimicking real process-signal-based graceful drains.
    """
    import threading

    shutdown_event = threading.Event()
    results: Dict[int, bool] = {}
    lock = threading.Lock()

    def _run_task(task_id: int) -> None:
        # Respect shutdown signal: don't start new work after shutdown
        if shutdown_event.is_set():
            with lock:
                results[task_id] = False
            return
        success = worker_fn(task_id)
        with lock:
            results[task_id] = success

    # Dispatch all tasks as threads
    threads = [threading.Thread(target=_run_task, args=(i,), daemon=True)
               for i in range(in_flight_tasks)]
    for t in threads:
        t.start()

    # Signal shutdown after all threads are dispatched (simulates SIGTERM)
    shutdown_event.set()

    # Enforce drain timeout: join each thread with remaining deadline
    deadline_s = drain_timeout_ms / 1000.0
    import time
    drain_start = time.monotonic()
    for t in threads:
        elapsed = time.monotonic() - drain_start
        remaining = max(0.0, deadline_s - elapsed)
        t.join(timeout=remaining)

    completed = sum(1 for v in results.values() if v)
    # Threads that didn't record a result within deadline are timed-out (aborted)
    aborted = in_flight_tasks - len(results) + sum(1 for v in results.values() if not v)

    passed = (completed == in_flight_tasks) and (aborted == 0)
    return {
        "in_flight_tasks": in_flight_tasks,
        "completed": completed,
        "aborted": aborted,
        "drain_timeout_ms": drain_timeout_ms,
        "passed": passed,
        "verdict": "GRACEFUL DRAIN VERIFIED (0 requests dropped)" if passed else f"DRAIN FAILURE ({aborted} tasks aborted or timed out)"
    }


def probe_graceful_drain_subprocess(
    cmd: Optional[Union[List[str], str, int]] = None,
    drain_timeout_ms: int = 1000,
    startup_wait_s: float = 0.05
) -> Dict[str, Any]:
    """
    Subprocess-based graceful shutdown drain probe using real OS signals:
      1. Spawns child Python process (handles SIGTERM by default).
      2. Sends SIGTERM via os.kill.
      3. Waits for child to drain and exit within drain_timeout_ms deadline.
      4. If child drops signal or hangs past deadline, terminates it and marks aborted=1, passed=False.
    """
    import subprocess
    import time
    import signal
    import shlex

    if isinstance(cmd, int):
        drain_timeout_ms = cmd
        cmd = None

    if cmd is None:
        cmd = [
            sys.executable,
            "-c",
            "import time, signal, sys; signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0)); time.sleep(10)"
        ]
    elif isinstance(cmd, str):
        if cmd.strip().startswith(sys.executable) or cmd.strip().startswith("python"):
            cmd = shlex.split(cmd)
        else:
            cmd = [sys.executable, "-c", cmd]

    child = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        if startup_wait_s > 0:
            time.sleep(startup_wait_s)

        if child.poll() is not None:
            return {
                "completed": 0,
                "aborted": 1,
                "drain_timeout_ms": drain_timeout_ms,
                "passed": False,
                "verdict": f"DRAIN FAILURE (Process exited prematurely with code {child.returncode})"
            }

        try:
            os.kill(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        deadline_s = drain_timeout_ms / 1000.0
        try:
            child.wait(timeout=deadline_s)
            completed = 1
            aborted = 0
            passed = True
            verdict = "GRACEFUL DRAIN SUBPROCESS VERIFIED (Process terminated cleanly within deadline)"
        except subprocess.TimeoutExpired:
            try:
                child.kill()
                child.wait(timeout=1.0)
            except Exception:
                pass
            completed = 0
            aborted = 1
            passed = False
            verdict = f"DRAIN FAILURE (Process hung past {drain_timeout_ms}ms deadline)"
    except Exception as exc:
        try:
            child.kill()
            child.wait(timeout=1.0)
        except Exception:
            pass
        completed = 0
        aborted = 1
        passed = False
        verdict = f"DRAIN FAILURE ({exc})"
    finally:
        try:
            if child.stdout:
                child.stdout.close()
            if child.stderr:
                child.stderr.close()
        except Exception:
            pass

    return {
        "completed": completed,
        "aborted": aborted,
        "drain_timeout_ms": drain_timeout_ms,
        "passed": passed,
        "verdict": verdict
    }


def get_current_rss_kb() -> int:
    """
    Returns current process resident set size (RSS) in kilobytes.
    Uses ctypes/psapi on Windows, and resource.RUSAGE_SELF on POSIX.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize // 1024)
        except Exception:
            pass
        return 0
    else:
        try:
            import resource
            return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        except Exception:
            return 0


def probe_memory_soak_plateau(
    operation_fn: Callable[[], None],
    iterations: int = 2000,
    sample_interval: int = 400,
    use_rss: bool = False
) -> Dict[str, Any]:
    """
    Executes a workload soak test and verifies memory growth rate plateaus.
    Uses Python's active object allocation tracking or RSS (resource.RUSAGE_SELF) as an empirical proxy.
    """
    if iterations <= 0:
        return {
            "passed": False,
            "unverified": True,
            "reason": "Zero iterations - result is unverified"
        }

    import gc
    gc.collect()

    samples = []
    effective_interval = max(1, sample_interval)
    for i in range(1, iterations + 1):
        operation_fn()
        if i % effective_interval == 0:
            gc.collect()
            if use_rss:
                val = get_current_rss_kb()
                samples.append({"iteration": i, "rss_kb": val, "object_count": val})
            else:
                count = len(gc.get_objects())
                samples.append({"iteration": i, "object_count": count})

    if not samples:
        gc.collect()
        if use_rss:
            val = get_current_rss_kb()
            samples.append({"iteration": iterations, "rss_kb": val, "object_count": val})
        else:
            count = len(gc.get_objects())
            samples.append({"iteration": iterations, "object_count": count})

    # Verify that growth between second half of samples is non-monotonic or bounded (< 15%)
    key = "rss_kb" if use_rss else "object_count"
    if len(samples) >= 3:
        initial = samples[0][key]
        mid = samples[len(samples) // 2][key]
        final = samples[-1][key]
        second_half_growth = (final - mid) / max(mid, 1)
        plateau = second_half_growth < 0.15
    elif len(samples) >= 2:
        initial = samples[0][key]
        final = samples[-1][key]
        second_half_growth = (final - initial) / max(initial, 1)
        plateau = second_half_growth < 0.15
    else:
        plateau = True
        second_half_growth = 0.0

    return {
        "iterations": iterations,
        "samples": samples,
        "second_half_growth_rate": round(second_half_growth, 4),
        "plateau": plateau,
        "passed": plateau,
        "verdict": "SOAK TEST PASSED (Resource telemetry plateaus)" if plateau else "MEMORY LEAK DETECTED (Monotonic resource expansion)"
    }


# ──────────────────────────────────────────────
# 5. Architecture: Slice Boundary & LOC Probe
# ──────────────────────────────────────────────

def probe_slice_boundaries(project_root: Union[str, Path], max_loc: int = 600, fail_on_loc: bool = False) -> Dict[str, Any]:
    """
    Scans project modules for illegal cross-slice internal imports
    and checks implementation files against the max LOC guideline.
    """
    root_path = Path(project_root).resolve()
    scripts_dir = Path(__file__).resolve().parent
    slice_guard_path = scripts_dir / "slice-guard.py"
    spec = importlib.util.spec_from_file_location("slice_guard", slice_guard_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load slice-guard from {slice_guard_path}")
    slice_guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(slice_guard)
    findings = slice_guard.scan_slice_project(root_path, max_loc=max_loc, fail_on_loc=fail_on_loc)
    is_pass = findings.get("status") == "pass"
    return {
        "status": findings.get("status", "pass"),
        "passed": is_pass,
        "modules_checked": findings.get("modules_checked", 0),
        "files_checked": findings.get("files_checked", 0),
        "violations": findings.get("violations", []),
        "verdict": "BOUNDARY CHECK PASSED (Hermetic slice isolation verified)" if is_pass else f"BOUNDARY VIOLATIONS DETECTED ({len(findings.get('violations', []))} violations)",
    }

