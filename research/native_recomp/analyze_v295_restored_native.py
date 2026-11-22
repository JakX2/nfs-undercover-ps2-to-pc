#!/usr/bin/env python3
"""V295: original-free classifier for bounded owner-private restored NAND trial.

Only sanitized counters and the process exit category leave CI. A successful
classification is not a claim that a restored function returned or booted.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

CHILD = re.compile(
    r"^V289_NAND_ENTRY n=([0-9]{1,4}) phase=[01] zero=[01] "
    r"sc=[0-9]{1,3} guest=([01]) inst=[0-9]{1,18}$"
)
WRITER = re.compile(
    r"^V278_FCA4_ENTRY n=([0-9]{1,4}) phase=[01] cb=[01] "
    r"nand=[01] child=[01] sc=[0-9]{1,3} guest=([01]) "
    r"inst=[0-9]{1,18}$"
)
CALLBACK = re.compile(r"^V250_CB_BEGIN candidate=1 reply=[01] captured=1$")
TRIAL = re.compile(r"^V[0-9]{2,3}_TRIAL_PASS trial=([0-9]{1,2})$")

def classify(output: str, returncode: int) -> tuple[str, bool]:
    if not 0 <= returncode <= 255:
        raise ValueError("invalid_exit_code")
    if len(output) > 8_000_000:
        raise ValueError("oversized_output")
    if returncode in (125, 126, 127):
        category = "launch_failure"
    elif returncode == 124:
        category = "timeout"
    elif returncode >= 128:
        category = "signal"
    elif returncode == 0:
        category = "exit_zero"
    else:
        category = "exit_nonzero"
    lines = output.splitlines()
    child = [m for line in lines if (m := CHILD.fullmatch(line))]
    writer = [m for line in lines if (m := WRITER.fullmatch(line))]
    callbacks = sum(bool(CALLBACK.fullmatch(line)) for line in lines)
    trials = len(set(int(m.group(1)) for line in lines if
                     (m := TRIAL.fullmatch(line))))
    valid_child = all(m.group(2) == "1" for m in child)
    valid_writer = all(m.group(2) == "1" for m in writer)
    observed = bool(child and valid_child)
    useful = category != "launch_failure" and callbacks > 0 and (
        observed or bool(writer))
    safe = useful and valid_writer and valid_child
    result = (
        f"V295_NATIVE_OUTCOME class={category} rc={returncode} "
        f"callbacks={callbacks} nand_entries={len(child)} "
        f"writer_entries={len(writer)} trial_passes={trials} "
        f"guest_observed={int(observed)} completed={int(returncode == 0)}"
    )
    return result, safe

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_log", type=Path)
    parser.add_argument("returncode", type=int)
    args = parser.parse_args()
    try:
        log = args.private_native_log.read_text(encoding="utf-8", errors="replace")
        summary, valid = classify(log, args.returncode)
    except (OSError, ValueError):
        print("V295_EXEC_AUDIT verified=0", file=sys.stderr)
        return 1
    print(summary)
    print(f"V295_EXEC_AUDIT verified={int(valid)}")
    return 0 if valid else 1

if __name__ == "__main__":
    sys.exit(main())
