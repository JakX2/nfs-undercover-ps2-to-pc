#!/usr/bin/env python3
"""V279 SHA-pinned Wii NAND-child -> SYSCONF writer BL guard audit.

Find authentic 0x8052FA60 direct BL to 0x8052FCA4 and any
earlier conditional branch targeting beyond the call. A possible
static skip does not prove that the branch executes natively.
No original instruction words or proprietary code are emitted.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc

CHILD=0x8052fa60
WRITER=0x8052fca4

def classify(words:list[int],pc:int)->dict[str,int]:
    if pc!=CHILD or not 8<=len(words)<=8192:
        raise ValueError("geometry")
    callsites=[
        i for i,w in enumerate(words)
        if (w>>26)==18 and (w&1)
        and branch_target(pc+4*i,w)==WRITER
    ]
    if len(callsites)!=1:raise ValueError("callsite_count")
    call_i=callsites[0]
    call_pc=pc+4*call_i
    skips=[]
    for i,w in enumerate(words[:call_i]):
        if w>>26!=16:continue
        source=pc+4*i
        dest=branch_target(source,w)
        if dest is not None and source<call_pc<dest<=pc+4*len(words):
            skips.append((i,dest,w))
    result=dict(call_offset=call_i*4,skip_cond=len(skips),
                nearest_skip_offset=-1,nearest_target_offset=-1,
                bo=-1,bi=-1,cr_expected=-1,cr_field=-1,
                producer_kind=0,producer_ra=-1,producer_imm_class=-1)
    if not skips:return result
    i,dest,w=skips[-1]
    edge=decode_bc(w)
    result.update(
        nearest_skip_offset=i*4,nearest_target_offset=dest-pc,
        bo=edge.bo,bi=edge.bi,cr_field=edge.cr_field,
        cr_expected=-1 if edge.cr_expected is None else int(edge.cr_expected),
    )
    if i==0:return result
    prev=words[i-1]
    op=prev>>26
    bf=(prev>>23)&7
    if op in (10,11) and bf==edge.cr_field:
        imm=prev&0xffff
        result.update(producer_kind=1 if op==11 else 2,
                      producer_ra=(prev>>16)&31,
                      producer_imm_class={0:0,1:1,2:2,3:3}.get(imm,4))
    elif op==31 and ((prev>>1)&1023) in (0,32) and bf==edge.cr_field:
        result.update(producer_kind=3,producer_ra=(prev>>16)&31)
    return result

def audit(data:bytes)->dict[str,int]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000 or WRITER not in functions:
        raise ValueError("symbols")
    n=functions.get(CHILD,0)
    if n<32 or n>32768 or n%4:
        raise ValueError("child_bounds")
    return classify(read_words(data,CHILD,n//4),CHILD)

def sanitized(v:dict[str,int])->str:
    keys=("call_offset","skip_cond","nearest_skip_offset",
          "nearest_target_offset","bo","bi","cr_expected",
          "cr_field","producer_kind","producer_ra","producer_imm_class")
    return "V279_NAND_SC_CALL child=8052fa60 writer=8052fca4 direct=1 "+\
           " ".join(f"{k}={v[k]}" for k in keys)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: output=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V279_NAND_CALL_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V279_NAND_CALL_AUDIT verified=1")
    print(sanitized(output))
    return 0

if __name__=="__main__":
    sys.exit(main())
