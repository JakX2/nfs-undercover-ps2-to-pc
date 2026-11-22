#!/usr/bin/env python3
"""V287: SHA-verified Wii NAND-child entry prefix control flow.

Inspect original child 0x8052FA60 before the early guarded service
BL at +0x50. Classify only direct call targets and potential forward
branches, with original PPC instruction bytes retained privately.
Static call presence does not prove a native executed path.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from audit_v279_nand_writer_guard import CHILD
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc

BOUND=80

def classify(words:list[int])->list[str]:
    if len(words)<48 or len(words)>8192:
        raise ValueError("geometry")
    prefix=words[:BOUND//4]
    calls=[]
    branches=[]
    for i,word in enumerate(prefix):
        op=word>>26
        pc=CHILD+i*4
        if op==18 and word&1:
            target=branch_target(pc,word)
            if target is not None:
                calls.append((i*4,target))
        elif op==16:
            target=branch_target(pc,word)
            if target is None:continue
            edge=decode_bc(word)
            prev=words[i-1] if i else 0
            cmpkind=0
            ra=-1
            immclass=-1
            field=-1
            if prev>>26 in (10,11):
                cmpkind=1 if prev>>26==11 else 2
                field=(prev>>23)&7
                ra=(prev>>16)&31
                imm=prev&0xffff
                immclass={0:0,1:1,2:2,3:3}.get(imm,4)
            branches.append(
                (i*4,target-CHILD,edge.bo,edge.bi,
                 -1 if edge.cr_expected is None else int(edge.cr_expected),
                 cmpkind,field,ra,immclass))
    rows=[
        f"V287_NAND_PREFIX child=8052fa60 bytes={BOUND} "
        f"calls={len(calls)} conditional={len(branches)} "
        f"forward_beyond_early={sum(dst>BOUND for _,dst,*_ in branches)}"
    ]
    for rank,(off,dest) in enumerate(calls,1):
        rows.append(f"V287_PREFIX_CALL rank={rank} offset={off} target={dest:08x}")
    for rank,(off,dest,bo,bi,expected,kind,field,ra,imm) in enumerate(branches,1):
        rows.append(
            f"V287_PREFIX_BRANCH rank={rank} offset={off} "
            f"dest_offset={dest} bo={bo} bi={bi} cr_expected={expected} "
            f"prev_cmp_kind={kind} cmp_field={field} cmp_ra={ra} imm_class={imm}"
        )
    return rows

def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000:raise ValueError("symbols")
    size=funcs.get(CHILD,0)
    if size<BOUND or size>32768 or size&3:
        raise ValueError("child_bounds")
    return classify(read_words(data,CHILD,size//4))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: rows=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V287_PREFIX_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V287_PREFIX_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
