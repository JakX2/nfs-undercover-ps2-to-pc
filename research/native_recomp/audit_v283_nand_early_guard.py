#!/usr/bin/env python3
"""V283: original Wii NAND-child early skip around guarded status writer.

Private SHA-256 verified ELF32 PowerPC words are decoded to sanitized
branch metadata and local CR producer categories only. Two static
forward skips around child->status-writer BL are expected from V279.
Neither branch is assumed dynamically taken until guest execution proves it.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys

from audit_v279_nand_writer_guard import CHILD,WRITER,classify as prior
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc

def classify(words:list[int])->list[str]:
    old=prior(words,CHILD)
    if old["call_offset"]!=184 or old["skip_cond"]!=2:
        raise ValueError("expected_two_guards")
    call_pc=CHILD+old["call_offset"]
    candidates=[]
    for i,w in enumerate(words[:old["call_offset"]//4]):
        if w>>26!=16:continue
        pc=CHILD+i*4
        target=branch_target(pc,w)
        if target is None or not pc<call_pc<target<=CHILD+4*len(words):
            continue
        candidates.append((i,target,w))
    if len(candidates)!=2:
        raise ValueError("guard_geometry")
    result=[]
    for rank,(i,target,w) in enumerate(candidates,1):
        edge=decode_bc(w)
        prev=words[i-1] if i else 0
        op=prev>>26
        producer=0
        ra=-1
        rb=-1
        immclass=-1
        field=-1
        if op in (10,11):
            producer=1 if op==11 else 2
            field=(prev>>23)&7
            ra=(prev>>16)&31
            immclass={0:0,1:1,2:2,3:3,0xffff:4}.get(prev&0xffff,5)
        elif op==31 and ((prev>>1)&1023) in (0,32):
            producer=3
            field=(prev>>23)&7
            ra=(prev>>16)&31
            rb=(prev>>11)&31
        result.append(
            f"V283_NAND_GUARD rank={rank} child=8052fa60 "
            f"branch_offset={i*4} target_offset={target-CHILD} "
            f"call_offset={old['call_offset']} bo={edge.bo} bi={edge.bi} "
            f"cr_field={edge.cr_field} cr_bit={edge.cr_bit} "
            f"cr_expected={-1 if edge.cr_expected is None else int(edge.cr_expected)} "
            f"ctr_decrement={int(edge.ctr_decrement)} "
            f"producer={producer} cmp_field={field} cmp_ra={ra} cmp_rb={rb} "
            f"imm_class={immclass} direct_cr={int(producer!=0 and field==edge.cr_field)}")
    return result

def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000 or WRITER not in funcs:
        raise ValueError("symbols")
    size=funcs.get(CHILD,0)
    if size<32 or size>32768 or size&3:
        raise ValueError("child_bounds")
    return classify(read_words(data,CHILD,size//4))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: rows=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V283_GUARD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V283_GUARD_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
