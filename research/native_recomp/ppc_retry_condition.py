#!/usr/bin/env python3
"""Original-free PowerPC condition producer at the V265 retry branch.

Classify instruction immediately before the authenticated CR0.EQ backedge.
Do not infer dataflow across unknown CR writes. Synthetic unit tests use
independently encoded PPC32 words; private ELF words never leave owner CI.
"""
from __future__ import annotations
from audit_v243_original_callback_branch import branch_target
from ppc_retry_edge import decode_bc, classify_retry_window


def classify_condition(start: int, words: list[int], callsite: int) -> dict[str, int]:
    edges = classify_retry_window(start, words, callsite)
    if (edges["backedge_count"] != 1 or edges["bo"] != 12 or
            edges["bi"] != 2 or edges["back_span"] != 8):
        raise ValueError("unverified_edge")
    candidates=[]
    for i,word in enumerate(words):
        pc=start+4*i
        if (word>>26)!=16:
            continue
        dest=branch_target(pc,word)
        if dest is not None and start<=dest<=callsite and dest<pc:
            candidates.append((i,pc,dest))
    if len(candidates)!=1 or candidates[0][0]<1:
        raise ValueError("backedge_geometry")
    i,pc,dest=candidates[0]
    previous=words[i-1]
    op=previous>>26
    # Producer categories: immediate (10,11), register (31/xo 0,32),
    # or andi./andis. record (28,29). Otherwise classify as unknown.
    kind=0
    bf=-1
    ra=-1
    rb=-1
    immediate_zero=-1
    if op in (10,11):
        kind=1 if op==11 else 2
        bf=(previous>>23)&7
        ra=(previous>>16)&31
        immediate_zero=int((previous&0xffff)==0)
    elif op==31 and ((previous>>1)&1023) in (0,32):
        kind=3 if ((previous>>1)&1023)==0 else 4
        bf=(previous>>23)&7
        ra=(previous>>16)&31
        rb=(previous>>11)&31
    elif op in (28,29):
        kind=5
        bf=0
        ra=(previous>>16)&31
        immediate_zero=int((previous&0xffff)==0)
    return {
        "backedge_from": pc-callsite,
        "backedge_to": dest-callsite,
        "prev_distance": 4,
        "producer_kind":kind,
        "producer_cr_field":bf,
        "producer_ra":ra,
        "producer_rb":rb,
        "producer_imm_zero":immediate_zero,
        "compares_helper_r3":int(
            pc-callsite==8 and kind in (1,2,3,4)
            and bf==0 and ra==3 and
            (immediate_zero==1 or rb>=0)),
    }


def sanitized(stats:dict[str,int])->str:
    keys=("backedge_from","backedge_to","prev_distance",
          "producer_kind","producer_cr_field","producer_ra",
          "producer_rb","producer_imm_zero","compares_helper_r3")
    return "V266_CONDITION "+" ".join(f"{k}={stats[k]}" for k in keys)
