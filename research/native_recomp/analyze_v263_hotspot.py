#!/usr/bin/env python3
"""V263: correlate real post-NAND PPC function-call recurrence and IRQ state.

The owner-only raw log contains 16 complete 64-call V261/V262 windows.
The public result gives only aggregate PC/LR pair counts and guest
instruction-count recurrence gaps. No instruction words, original DOL
bytes, translated game code, or guest memory are exposed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from statistics import median_low
import sys

from analyze_v261_postipc_calls import (
    CALLS, TRIALS, FINAL_PC, FINAL_LR, census, parse_trials
)
from analyze_v262_ipc_state import parse as parse_states

RESTORE_PC = 0x805265D4
DISABLE_PC = 0x805265AC
REASONS = {
    "unstable_guest_calls", "unstable_ios_state", "invalid_call_count",
    "invalid_pair_rank", "unexpected_call_frontier",
    "malformed_call_marker", "nonsequential_call_marker",
    "nonmonotonic_instruction_counter", "unverified_frontier",
    "incomplete_call_trace", "wrong_trial_count",
    "malformed_state_marker", "out_of_order_state", "unmapped_sc_state",
    "frontier_sc_changed", "incomplete_state_window",
    "trial_count_changed", "wrong_call_count",
}


def analyze(log: str) -> tuple[str, tuple[str, ...]]:
    traces = parse_trials(log)
    states = parse_states(log)
    if len(traces) != TRIALS or len(states) != TRIALS:
        raise ValueError("invalid_call_count")
    ref = tuple((c.pc, c.lr) for c in traces[0])
    ref_state = states[0]
    if any(tuple((c.pc, c.lr) for c in t) != ref for t in traces[1:]):
        raise ValueError("unstable_guest_calls")
    if any(s != ref_state for s in states[1:]):
        raise ValueError("unstable_ios_state")
    if len(ref) != CALLS or ref[-1] != (FINAL_PC, FINAL_LR):
        raise ValueError("unexpected_call_frontier")
    counts = Counter(ref)
    ranks = sorted(counts, key=lambda pair: (-counts[pair], pair[0], pair[1]))
    if len(ranks) < 3:
        raise ValueError("invalid_pair_rank")
    first = census(traces[0])
    restoring = sum(pc == RESTORE_PC for pc, _ in ref)
    disabling = sum(pc == DISABLE_PC for pc, _ in ref)
    # Every guest instruction counter must be genuinely increasing.
    guest_insts = traces[0][-1].inst - traces[0][0].inst
    if guest_insts <= 0:
        raise ValueError("nonmonotonic_instruction_counter")
    summary = (
        f"V263_HOTSPOT trials={TRIALS} calls={CALLS} stable=1 "
        f"unique_pc={first['unique_pc']} unique_pairs={len(counts)} "
        f"max_freq={counts[ranks[0]]} restore_hits={restoring} "
        f"disable_hits={disabling} total_guest_inst={guest_insts} "
        f"irq_ever={int(any(x.irq for x in ref_state))} "
        f"request_ever={int(any(x.request for x in ref_state))} "
        f"sc_stable={int(len({x.sc for x in ref_state}) == 1)}"
    )
    lines = []
    for rank, pair in enumerate(ranks[:3], 1):
        positions = [i for i, p in enumerate(ref) if p == pair]
        gaps = [
            traces[0][right].inst - traces[0][left].inst
            for left, right in zip(positions, positions[1:])
        ]
        ee_on = sum(ref_state[i].ee for i in positions)
        lines.append(
            f"V263_PAIR rank={rank} pc={pair[0]:08x} lr={pair[1]:08x} "
            f"freq={len(positions)} first={positions[0]+1} "
            f"last={positions[-1]+1} first32={sum(i<32 for i in positions)} "
            f"last32={sum(i>=32 for i in positions)} "
            f"ee_on={ee_on} ee_off={len(positions)-ee_on} "
            f"gap_min={min(gaps) if gaps else 0} "
            f"gap_med={median_low(gaps) if gaps else 0} "
            f"gap_max={max(gaps) if gaps else 0}"
        )
    return summary, tuple(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_log", type=Path)
    args = parser.parse_args()
    try:
        output = analyze(args.private_native_log.read_text(
            encoding="utf-8", errors="replace"))
    except (OSError, ValueError) as err:
        reason = str(err)
        if reason not in REASONS:
            reason = "input_error"
        print(f"V263_HOTSPOT_ERROR reason={reason}", file=sys.stderr)
        return 1
    print(output[0])
    for line in output[1]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
