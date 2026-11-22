#!/usr/bin/env python3
"""Original-free PPC retry-edge CR/BO/BI classifier; prints no instruction bytes."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Edge:
    conditional: bool
    bo: int
    bi: int
    cr_field: int
    cr_bit: int
    ctr_decrement: bool
    ctr_must_zero: bool | None
    cr_expected: bool | None

def decode_bc(word: int) -> Edge:
    if not 0 <= word <= 0xffffffff or word >> 26 != 16:
        raise ValueError("not_bc")
    bo = (word >> 21) & 31
    bi = (word >> 16) & 31
    # PowerPC BO bits: BO[0] skips CR; BO[2] skips CTR.
    skip_cr = bool(bo & 0x10)
    skip_ctr = bool(bo & 0x04)
    return Edge(True, bo, bi, bi // 4, bi % 4,
                not skip_ctr,
                None if skip_ctr else bool(bo & 0x02),
                None if skip_cr else bool(bo & 0x08))

def evaluate(edge: Edge, cr: int, ctr: int) -> tuple[bool, int]:
    if not 0 <= cr <= 0xffffffff or not 0 <= ctr <= 0xffffffff:
        raise ValueError("register")
    next_ctr = ((ctr - 1) & 0xffffffff) if edge.ctr_decrement else ctr
    ctr_ok = edge.ctr_must_zero is None or ((next_ctr == 0) == edge.ctr_must_zero)
    # BI=0 is the MSB of the architected CR.
    cr_bit = bool((cr >> (31 - edge.bi)) & 1)
    cr_ok = edge.cr_expected is None or cr_bit == edge.cr_expected
    return ctr_ok and cr_ok, next_ctr

def classify_retry_window(start: int, words: list[int], callsite: int) -> dict[str, int]:
    if start & 3 or callsite & 3 or not words or len(words) > 8192:
        raise ValueError("geometry")
    candidates = []
    for index, word in enumerate(words):
        pc = start + index * 4
        if word >> 26 != 16:
            continue
        disp = word & 0xfffc
        if disp & 0x8000:
            disp -= 0x10000
        dest = disp if word & 2 else pc + disp
        if dest <= callsite and dest < pc and start <= dest:
            candidates.append((pc, dest, decode_bc(word)))
    if len(candidates) != 1:
        raise ValueError("ambiguous_backedge")
    pc, dest, edge = candidates[0]
    return dict(backedge_count=1, back_span=pc-dest, bo=edge.bo, bi=edge.bi,
                cr_field=edge.cr_field, cr_bit=edge.cr_bit,
                ctr_decrement=int(edge.ctr_decrement),
                ctr_zero=-1 if edge.ctr_must_zero is None else int(edge.ctr_must_zero),
                cr_expected=-1 if edge.cr_expected is None else int(edge.cr_expected))

def sanitized(stats: dict[str, int]) -> str:
    fields=("backedge_count","back_span","bo","bi","cr_field","cr_bit",
            "ctr_decrement","ctr_zero","cr_expected")
    return "RETRY_EDGE " + " ".join(f"{key}={stats[key]}" for key in fields)
