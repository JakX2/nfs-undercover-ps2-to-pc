#!/usr/bin/env python3
"""Analyze bounded original Wii guest-call entries without publishing raw call logs.

Consumes the private owner CI log, accepts *only* the post-V259 64-entry
V261 traces, and emits a compact original-free structure summary. This is
an observational tool, not a guest-code or scheduler implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import sys

CALLS = 64
TRIALS = 16
FINAL_PC = 0x805265D4
FINAL_LR = 0x8052F92C
TRACE = re.compile(
    r"^V261_CALL n=([1-9]|[1-5][0-9]|6[0-4]) "
    r"pc=([0-9a-f]{8}) lr=([0-9a-f]{8}) inst=([0-9]+)$"
)


@dataclass(frozen=True)
class Call:
    pc: int
    lr: int
    inst: int


def parse_trials(log: str) -> list[tuple[Call, ...]]:
    trials: list[tuple[Call, ...]] = []
    active: list[Call] = []
    for line in log.splitlines():
        if not line.startswith("V261_CALL "):
            continue
        match = TRACE.fullmatch(line)
        if match is None:
            raise ValueError("malformed_call_marker")
        number, pc, lr, inst = match.groups()
        if int(number) != len(active) + 1:
            raise ValueError("nonsequential_call_marker")
        entry = Call(int(pc, 16), int(lr, 16), int(inst))
        if active and entry.inst <= active[-1].inst:
            raise ValueError("nonmonotonic_instruction_counter")
        active.append(entry)
        if len(active) == CALLS:
            if (entry.pc, entry.lr) != (FINAL_PC, FINAL_LR):
                raise ValueError("unverified_frontier")
            trials.append(tuple(active))
            active = []
    if active:
        raise ValueError("incomplete_call_trace")
    if len(trials) != TRIALS:
        raise ValueError("wrong_trial_count")
    return trials


def census(calls: tuple[Call, ...]) -> dict[str, int | str]:
    if len(calls) != CALLS:
        raise ValueError("wrong_call_count")
    pairs = [(c.pc, c.lr) for c in calls]
    freq = Counter(pairs)
    first = set(pairs[:32])
    packed = b"".join(c.pc.to_bytes(4, "big") + c.lr.to_bytes(4, "big") for c in calls)
    return {
        "unique_pc": len({c.pc for c in calls}),
        "unique_pairs": len(freq),
        "repeated": CALLS - len(freq),
        "new_second": len(set(pairs[32:]) - first),
        "match32": sum(pairs[i] == pairs[i + 32] for i in range(32)),
        "max_freq": max(freq.values()),
        "digest": hashlib.sha256(packed).hexdigest()[:16],
        "first_pc": f"{calls[0].pc:08x}",
        "last_pc": f"{calls[-1].pc:08x}",
        "last_lr": f"{calls[-1].lr:08x}",
    }


def summarize(trials: list[tuple[Call, ...]]) -> str:
    if len(trials) != TRIALS:
        raise ValueError("wrong_trial_count")
    summaries = [census(calls) for calls in trials]
    distinct = len({entry["digest"] for entry in summaries})
    stats = summaries[0]
    return (
        f"V261_CENSUS trials={TRIALS} calls={CALLS} "
        f"stable={int(distinct == 1)} distinct={distinct} "
        f"unique_pc={stats['unique_pc']} unique_pairs={stats['unique_pairs']} "
        f"repeated={stats['repeated']} new_second={stats['new_second']} "
        f"match32={stats['match32']} max_freq={stats['max_freq']} "
        f"monotonic=1 digest={stats['digest']} "
        f"first_pc={stats['first_pc']} last_pc={stats['last_pc']} "
        f"last_lr={stats['last_lr']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_log", type=Path)
    args = parser.parse_args()
    try:
        log = args.private_log.read_text(encoding="utf-8", errors="replace")
        print(summarize(parse_trials(log)))
    except (OSError, ValueError) as error:
        kind = str(error)
        if kind not in {
            "malformed_call_marker", "nonsequential_call_marker",
            "nonmonotonic_instruction_counter", "unverified_frontier",
            "incomplete_call_trace", "wrong_trial_count", "wrong_call_count",
        }:
            kind = "input_error"
        print(f"V261_CENSUS_ERROR reason={kind}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
