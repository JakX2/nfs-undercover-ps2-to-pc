#!/usr/bin/env python3
"""Run a private native-Wii test command and record a safe boot checkpoint.

This script executes a supplied test runner. It does NOT execute guest PowerPC,
translate a DOL, or infer a checkpoint from a successful exit. Only an explicit
BOOT_PROGRESS line emitted by a successful native runner proves the guest PC.

No command arguments, absolute paths, raw logs, game bytes, or game-derived
C++ are included in the machine-readable report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

MARKER = re.compile(
    r"^BOOT_PROGRESS entry=(0x[0-9a-fA-F]{8}) pc=(0x[0-9a-fA-F]{8})"
    r"(?: stage=([0-9]+))?$"
)
LANE_ENTRY = {"continuous-start": 0x8000403C, "osinit-direct": 0x80520670}
MAX_CAPTURE = 1_048_576  # Only a checksum and allowlisted markers are reported.
# Diagnostic names are original-free, fixed runner stages. Never echo arbitrary
# subprocess output, file paths, disassembly, generated game code or messages.
SAFE_RUNNER_STAGES = {
    "V35": ("v29_runtime_verified", "hid4_runtime_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V36": ("v29_runtime_verified", "hid4_runtime_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V37": ("v29_runtime_verified", "hid4_runtime_verified", "fixture_generated",
            "geometry_verified", "negative_guards_verified",
            "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V38": ("v29_runtime_verified", "hid4_runtime_verified", "fixture_generated",
            "geometry_verified", "negative_guards_verified",
            "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V39": ("v29_runtime_verified", "hid4_runtime_verified",
            "cache_patch_verified", "fixture_generated", "geometry_verified",
            "generator_compiled", "generation_complete", "native_compiled",
            "native_test_passed", "fixture_collision", "fixture_stop_collision",
            "fixture_section", "fixture_source", "fixture_inherited",
            "fixture_other", "inherited_fixture_ready",
            "original_cache_calls_verified", "original_cache_bodies_verified",
            "cache_sections_mapped", "cache_helpers_installed",
            "bounded_stop_installed", "os_section_verified",
            "previous_stop_verified", "cache_section_verified",
            "fixture_os_section", "fixture_previous_stop", "fixture_cache_section"),
    "V40": ("v29_runtime_verified", "hid4_runtime_verified",
            "cache_patch_verified", "cache_trace_verified",
            "fixture_generated", "geometry_verified", "generator_compiled",
            "generation_complete", "native_compiled", "native_test_passed",
            "fixture_collision", "fixture_stop_collision", "fixture_section",
            "fixture_source", "fixture_inherited", "fixture_other",
            "fixture_os_section", "fixture_previous_stop", "fixture_cache_section"),
    "V41": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V42": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V43": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V44": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V45": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V46": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V47": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V48": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V49": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V50": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V51": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V52": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V53": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V54": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V55": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V56": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V57": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V58": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V59": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V60": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V61": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V62": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V63": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V64": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V65": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V66": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
    "V67": ("runtime_cache_trace_verified", "fixture_generated",
            "geometry_verified", "generator_compiled", "generation_complete",
            "native_compiled", "native_test_passed"),
}


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_markers(text: str) -> tuple[list[dict], int]:
    observations = []
    passes = 0
    for line in text.splitlines():
        if line.startswith("PASS:"):
            passes += 1
        match = MARKER.fullmatch(line.strip())
        if match:
            observations.append({
                "entry": int(match[1], 16),
                "pc": int(match[2], 16),
                "stage": int(match[3]) if match[3] is not None else None,
            })
    return observations, passes


def save_report(output: Path, report: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix=".boot-report-", dir=output.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as target:
            json.dump(report, target, indent=2, sort_keys=True)
            target.write("\n")
        os.replace(filename, output)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


def run(args: argparse.Namespace) -> int:
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("a command after -- is required")
    if args.timeout <= 0:
        raise ValueError("timeout must be positive")
    if args.lane == "continuous-start" and args.expected_entry not in (None, 0x8000403C):
        raise ValueError("continuous-start must enter at original __start (0x8000403C)")
    if args.lane == "osinit-direct" and args.expected_entry not in (None, 0x80520670):
        raise ValueError("osinit-direct must enter at original OSInit (0x80520670)")
    entry = args.expected_entry if args.expected_entry is not None else LANE_ENTRY.get(args.lane)
    if args.dol is not None and args.sha256 is None:
        raise ValueError("owner DOL requires an expected SHA-256; refusing unpinned private fixture")
    if args.sha256 is not None and args.dol is None:
        raise ValueError("--sha256 requires --dol")
    # Never replace the pinned input or baseline with the result, even via a symlink.
    protected = (path for path in (args.dol, args.baseline) if path is not None)
    if any(args.report.resolve() == path.resolve() for path in protected):
        raise ValueError("report path aliases a read-only input")
    if args.dol is not None and hash_file(args.dol).lower() != args.sha256.lower():
        raise ValueError("private owner DOL SHA-256 mismatch; command not executed")

    baseline = None
    if args.baseline is not None:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline.get("schema") != "undercover-boot-progress-v1":
            raise ValueError("unsupported checkpoint baseline schema")
        if baseline.get("lane") != args.lane:
            raise ValueError("baseline lane differs; never compare __start with direct OSInit")
        if baseline.get("status") not in ("passed_instrumented", "advanced"):
            raise ValueError("baseline is not a verified checkpoint")
        pc, stage = baseline.get("observed_pc"), baseline.get("stage")
        if (type(pc) is not int or not 0 <= pc <= 0xFFFFFFFF or
                type(stage) is not int or stage < 0):
            raise ValueError("baseline lacks a valid instrumented PC and stage")
        if entry is not None and baseline.get("observed_entry") != entry:
            raise ValueError("baseline entry does not match this execution lane")
        if baseline.get("owner_image_sha256") != args.sha256:
            raise ValueError("baseline owner DOL SHA-256 differs from current input")
    if args.require_progress and baseline is None:
        raise ValueError("--require-progress requires a verified --baseline")

    began = time.monotonic()
    rc = None
    timed_out = False
    stdout = ""
    stderr = ""
    try:
        done = subprocess.run(command, capture_output=True, text=True,
                              errors="replace", timeout=args.timeout,
                              cwd=args.cwd, check=False)
        rc, stdout, stderr = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    except OSError as exc:
        stderr = f"{type(exc).__name__}: launch failed"
    elapsed = round(time.monotonic() - began, 3)
    observations, passes = parse_markers(stdout)
    stderr_observations, stderr_passes = parse_markers(stderr)
    observations.extend(stderr_observations)
    passes += stderr_passes
    # Multiple distinct guest PCs on one test command are not a single verified stop.
    consistent = len({(o["entry"], o["pc"], o["stage"]) for o in observations}) <= 1
    observed = observations[0] if observations and consistent else None
    status = "failed"
    reason = None
    if timed_out:
        reason = "timeout"
    elif rc != 0:
        reason = "runner_failed"
    elif passes == 0:
        reason = "no_native_pass_marker"
    elif not consistent:
        reason = "conflicting_guest_checkpoints"
    elif observed is not None and entry is not None and observed["entry"] != entry:
        reason = "unexpected_entry"
    elif args.expected_pc is not None and (observed is None or observed["pc"] != args.expected_pc):
        reason = "expected_stop_not_observed"
    elif args.require_progress and observed is None:
        reason = "no_guest_checkpoint"
    elif args.require_progress and (observed["stage"] is None or observed["stage"] <= baseline["stage"]):
        reason = "no_verified_stage_advance"
    elif args.require_progress and observed["pc"] == baseline["observed_pc"]:
        reason = "stop_pc_unchanged"
    else:
        if observed is None:
            status = "passed_uninstrumented"  # PASS is real; guest checkpoint is not observed.
        else:
            status = "advanced" if args.require_progress else "passed_instrumented"
    # Failed native assertions, timeouts and conflicting markers cannot
    # establish a verified guest-PC checkpoint, even if a marker was printed.
    if reason is not None:
        observed = None
    report = {
        "schema": "undercover-boot-progress-v1",
        "lane": args.lane,
        "status": status,
        "failure_reason": reason,
        "exit_code": rc,
        "timed_out": timed_out,
        "elapsed_s": elapsed,
        "pass_markers": passes,
        "expected_entry": entry,
        "observed_entry": observed["entry"] if observed else None,
        "observed_pc": observed["pc"] if observed else None,
        "stage": observed["stage"] if observed else None,
        "expected_stop_pc": args.expected_pc,
        "owner_image_sha256": args.sha256.lower() if args.sha256 else None,
        "failure_output_sha256": hashlib.sha256((stdout[-MAX_CAPTURE:] + stderr[-MAX_CAPTURE:]).encode()).hexdigest() if reason else None,
    }
    save_report(args.report, report)
    stop = f"0x{observed['pc']:08X}" if observed else "unobserved"
    print(f"BOOT_RESULT status={status} lane={args.lane} pc={stop} passes={passes}"
          + (f" reason={reason}" if reason else ""))
    if reason is None and args.diagnostic_runner == "V65" and observed and observed["stage"] == 65:
        census = [re.fullmatch(r"V632_MAPPER_MODES entry=([0-9]{1,2}(?:,[0-9]{1,2}){3}) return=([0-9]{1,2}(?:,[0-9]{1,2}){3}) trials=16", line)
                  for line in stdout.splitlines()]
        census = [m for m in census if m]
        if len(census) == 1 and all(sum(map(int, census[0][i].split(","))) == 16 for i in (1, 2)):
            print(census[0][0])
    if reason is not None and args.diagnostic_runner is not None:
        prefix = args.diagnostic_runner
        allowed = SAFE_RUNNER_STAGES[prefix]
        lines = set(stdout.splitlines()) | set(stderr.splitlines())
        for stage in allowed:
            if prefix + "_STAGE " + stage in lines:
                print(f"BOOT_DIAGNOSTIC stage={prefix}.{stage}")
        if prefix in ("V35", "V36", "V37", "V38", "V39", "V40", "V41", "V42", "V43", "V44", "V45", "V46", "V47", "V48", "V49", "V50", "V51", "V52", "V53", "V54", "V55", "V56", "V57", "V58", "V59", "V60", "V61", "V62", "V63", "V64", "V65", "V66", "V67"):
            # A bounded numeric ID derived only from the public original-free
            # harness assertion literals. Never surface the private log itself.
            valid = re.compile(rf"^{prefix}_NATIVE_ASSERTION id=([0-9]{{3}})$")
            for line in lines:
                match=valid.fullmatch(line)
                if match:
                    print(f"BOOT_DIAGNOSTIC assertion_id={prefix}.{match[1]}")
                    break
    return 0 if status in ("advanced", "passed_instrumented", "passed_uninstrumented") else 1


def hex_address(value: str) -> int:
    number = int(value, 0)
    if not 0 <= number <= 0xFFFFFFFF:
        raise argparse.ArgumentTypeError("guest address must be 32-bit")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lane", required=True, choices=["continuous-start", "osinit-direct", "synthetic"])
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--cwd", type=Path, default=None)
    parser.add_argument("--expected-entry", type=hex_address)
    parser.add_argument("--expected-pc", type=hex_address)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--require-progress", action="store_true")
    parser.add_argument("--diagnostic-runner", choices=tuple(SAFE_RUNNER_STAGES),
                        help="print only allowlisted original-free stage labels on failure")
    parser.add_argument("--dol", type=Path)
    parser.add_argument("--sha256", type=lambda s: s.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", s) else (_ for _ in ()).throw(argparse.ArgumentTypeError("invalid SHA-256")))
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- program arguments (never persisted)")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"BOOT_RESULT status=setup_error reason={type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
