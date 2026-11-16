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
    if args.dol is not None and hash_file(args.dol).lower() != args.sha256.lower():
        raise ValueError("private owner DOL SHA-256 mismatch; command not executed")

    baseline = None
    if args.baseline is not None:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if baseline.get("lane") != args.lane:
            raise ValueError("baseline lane differs; never compare __start with direct OSInit")
        if baseline.get("status") not in ("passed_instrumented", "advanced"):
            raise ValueError("baseline is not a verified checkpoint")
        if baseline.get("observed_pc") is None or baseline.get("stage") is None:
            raise ValueError("baseline lacks an instrumented PC and stage")
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
