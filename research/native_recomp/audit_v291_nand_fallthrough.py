#!/usr/bin/env python3
"""V291: find original NAND branch/CR0 changes before early service BL.

V289 (corrected) observed 16/16 incoming r3==0; V290 SHA-verified
that both instructions preceding original cmpwi r3,0 preserve r3.
Audit three instructions between that comparison and bne +92, then
all control transfers between the fallthrough +28 and service BL +80.
This is static control-flow evidence, not proof that a branch executed.
The original executable remains private; never emit PPC words.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from audit_v279_nand_writer_guard import CHILD
from audit_v290_nand_input_liveness import classify as r3_classify
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc

def cr0_effect(word):
    """Return keep/write/unknown/control conservatively."""
    op=word>>26
    xo=(word>>1)&1023
    bf=(word>>23)&7
    if op in (16,17,18):return "control"
    if op==19:
        if xo in (16,528):return "control"
        return "unknown"
    if op in (10,11):return "write" if bf==0 else "keep"
    if op in (28,29):return "write"
    if op in (20,21,23):return "write" if word&1 else "keep"
    if op==31:
        if xo in (0,32):return "write" if bf==0 else "keep"
        if xo==144:return "unknown" # mtcrf with mask
        if word&1:return "write" # record-flag PPC ALU family, conservative
        if xo in (339,467,19,23,55,87,151,183,215,247,279,343,407,439,444):
            return "keep"
        return "unknown"
    if op in (7,8,12,13,14,15,24,25,26,27,32,33,34,35,36,37,
              38,39,40,41,42,43,44,45,48,49,50,51,52,53,54,55):
        return "keep"
    return "unknown"

def scan(words):
    if not 48<=len(words)<=8192:raise ValueError("geometry")
    if "preserved=1" not in r3_classify(words):
        raise ValueError("entry_r3_not_preserved")
    effects=[cr0_effect(words[i]) for i in (3,4,5)]
    state="preserved" if effects==["keep"]*3 else (
        "clobbered" if "write" in effects else "inconclusive")
    flow=[]
    for i in range(7,20):
        word=words[i]
        op=word>>26
        pc=CHILD+4*i
        if op in (16,18):
            dest=branch_target(pc,word)
            kind=("conditional" if op==16 else "direct_call" if word&1 else "direct_jump")
            bo=((word>>21)&31) if op==16 else -1
            bi=((word>>16)&31) if op==16 else -1
            flow.append((4*i,kind,0 if dest is None else int(dest-CHILD),bo,bi))
        elif op==19 and ((word>>1)&1023) in (16,528):
            kind="lr" if ((word>>1)&1023)==16 else "ctr"
            flow.append((4*i,kind,-1,-1,-1))
        elif op==17:
            flow.append((4*i,"system",-1,-1,-1))
    kinds=("conditional","direct_call","direct_jump","lr","ctr","system")
    stats={k:sum(x[1]==k for x in flow) for k in kinds}
    result=[
        "V291_NAND_FALLTHROUGH child=8052fa60 cmp=8 branch=24 "
        f"service_call=80 cr0={state} "
        f"between_keep={effects.count('keep')} between_write={effects.count('write')} "
        f"between_unknown={effects.count('unknown')} between_control={effects.count('control')} "
        f"events={len(flow)} " +
        " ".join(f"{k}={stats[k]}" for k in kinds)
    ]
    for n,(off,k,dest,bo,bi) in enumerate(flow,1):
        result.append(
            f"V291_FLOW rank={n} offset={off} kind={k} "
            f"target_offset={dest} bo={bo} bi={bi}")
    return result

def audit(data):
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("original_sha")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    size=functions.get(CHILD,0)
    if size<192 or size>32768 or size&3:
        raise ValueError("geometry")
    return scan(read_words(data,CHILD,size//4))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    a=p.parse_args()
    try: rows=audit(a.private_owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V291_NAND_FLOW_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V291_NAND_FLOW_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
