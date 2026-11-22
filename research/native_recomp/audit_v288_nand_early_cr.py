#!/usr/bin/env python3
"""V288: original Wii NAND entry CR0 producer before the first forward skip.

The first original conditional edge at +0x18 skips the service at
+0x50. Decode the latest recognizable CR0 producer within earlier
straight-line instructions; unknown CR writers are explicitly
classified as uncertain. Only sanitized register fields leave
SHA-verified owner-private ELF analysis.
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

BRANCH_OFFSET=24
DEST_OFFSET=92

def producer(word:int)->tuple[str,int,int,int,int]:
    op=word>>26
    ra=(word>>16)&31
    rb=(word>>11)&31
    imm=word&0xffff
    if op in (10,11):
        return ("cmpimm" if op==11 else "cmplimm",
                (word>>23)&7,ra,-1,
                {0:0,1:1,2:2,3:3}.get(imm,4))
    if op==31:
        xo=(word>>1)&1023
        if xo in (0,32):
            return ("cmpreg" if xo==0 else "cmplreg",
                    (word>>23)&7,ra,rb,-1)
        if xo==144:
            return ("mtcrf",-1,ra,rb,-1)
        if word&1:
            return ("record",0,ra,rb,-1)
    if op in (28,29):
        return ("record",0,ra,rb,-1)
    if op in (20,21,23) and word&1:
        return ("record",0,ra,rb,-1)
    if op==19 and ((word>>1)&1023) not in (16,528):
        return ("crlogical",-1,ra,rb,-1)
    return ("none",-1,-1,-1,-1)

def classify(words:list[int])->str:
    if len(words)<48 or len(words)>8192:raise ValueError("geometry")
    i=BRANCH_OFFSET//4
    w=words[i]
    if w>>26!=16 or branch_target(CHILD+BRANCH_OFFSET,w)!=CHILD+DEST_OFFSET:
        raise ValueError("early_branch")
    edge=decode_bc(w)
    if edge.bo!=4 or edge.bi!=2 or edge.cr_expected is not False:
        raise ValueError("original_edge")
    result=("entry",-1,-1,-1,-1,-1)
    for j in range(i-1,-1,-1):
        wj=words[j]
        if wj>>26 in (16,17,18,19) and (wj>>26!=19 or ((wj>>1)&1023) in (16,528)):
            result=("barrier",j*4,-1,-1,-1,-1)
            break
        kind,field,ra,rb,imm=producer(wj)
        if kind!="none":
            result=(kind,j*4,field,ra,rb,imm)
            break
    kind,off,field,ra,rb,imm=result
    return (f"V288_EARLY_CR child=8052fa60 branch_offset={BRANCH_OFFSET} "
            f"skip_target={DEST_OFFSET} bo={edge.bo} bi={edge.bi} "
            f"cr_expected={int(edge.cr_expected)} "
            f"producer={kind} producer_offset={off} "
            f"cr_field={field} ra={ra} rb={rb} imm_class={imm}")

def audit(data:bytes)->str:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000:raise ValueError("symbols")
    n=funcs.get(CHILD,0)
    if n<192 or n>32768 or n&3:raise ValueError("bounds")
    return classify(read_words(data,CHILD,n//4))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: row=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V288_EARLY_CR_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V288_EARLY_CR_AUDIT verified=1")
    print(row)
    return 0

if __name__=="__main__":
    sys.exit(main())
