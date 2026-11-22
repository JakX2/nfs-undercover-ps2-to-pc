#!/usr/bin/env python3
"""V290: original NAND child entry r3 liveness through first cmpwi.

V288 established original compare r3,0 at +8, bne +92 at +24.
Decode two preceding PPC instructions with conservative GPR3-effect
rules before interpreting entry r3 as the branch input. Unknown
operations are *not* treated as preserving the input register.
Original ELF remains SHA-256 gated and private.
"""
import argparse
import hashlib
from pathlib import Path
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from audit_v279_nand_writer_guard import CHILD
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc

def effect(word):
    """Return (family, gpr3_effect) with keep/write/unknown/control."""
    op=word>>26
    rt=(word>>21)&31
    ra=(word>>16)&31
    xo=(word>>1)&1023
    if op in (16,17,18):return "branch","control"
    if op==19:return ("branch","control") if xo in (16,528) else ("cr","keep")
    if op in (10,11):return "compare","keep"
    if op in (36,38,44,54):return "store","keep"
    if op in (37,39,45,55):
        return "storeupdate","write" if ra==3 else "keep"
    if op in (7,8,12,13,14,15,32,33,34,35,40,41,42,43):
        return "result","write" if rt==3 else "keep"
    if op in (20,21,23,24,25,26,27,28,29):
        return "logical","write" if ra==3 else "keep"
    if op==31:
        if xo in (0,32,144,467):return "crspr","keep"
        if xo in (339,19,23,55,87,279,343):
            return "special","write" if rt==3 else "keep"
        if xo==444:return "or","write" if ra==3 else "keep"
        if xo in (151,183,215,247,407,439):
            return "indexedstore","keep"
        return "unknown31","unknown"
    return "unknown","unknown"

def classify(words):
    if not 8<=len(words)<=8192:raise ValueError("function_bounds")
    cmp=words[2]
    branch=words[6]
    if not (cmp>>26==11 and (cmp>>23)&7==0 and
            (cmp>>16)&31==3 and (cmp&0xffff)==0):
        raise ValueError("original_cmp")
    e=decode_bc(branch)
    if (branch>>26!=16 or branch_target(CHILD+24,branch)!=CHILD+92
            or e.bo!=4 or e.bi!=2 or e.cr_expected is not False):
        raise ValueError("original_branch")
    first=effect(words[0])
    second=effect(words[1])
    effects={first[1],second[1]}
    return (
        "V290_NAND_INPUT child=8052fa60 cmp=8 branch=24 target=92 "
        "nonzero_skips=1 zero_fallthrough=1 "
        f"preserved={int(effects=={'keep'})} "
        f"write={int('write' in effects)} unknown={int('unknown' in effects)} "
        f"control={int('control' in effects)} "
        f"i0={first[0]} e0={first[1]} i1={second[0]} e1={second[1]}"
    )

def audit(data):
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("original_sha")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    size=functions.get(CHILD,0)
    if not 32<=size<=32768 or size&3:raise ValueError("geometry")
    return classify(read_words(data,CHILD,size//4))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    a=p.parse_args()
    try: row=audit(a.private_owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V290_NAND_INPUT_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V290_NAND_INPUT_AUDIT verified=1")
    print(row)
    return 0

if __name__=="__main__":
    sys.exit(main())
