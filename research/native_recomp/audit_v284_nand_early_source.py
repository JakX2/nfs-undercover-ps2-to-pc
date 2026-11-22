#!/usr/bin/env python3
"""V284: original Wii NAND early zero-skip r3 producer, owner ELF only.

Verify both V283 exact original conditional edges before examining the
first branch's immediate CR producer (cmpwi r3, 0). Walk backward within
original function to nearest r3 assignment/service call, with no guest
memory writes or public original instruction words.
"""
import argparse
import hashlib
from pathlib import Path
import sys

from audit_v279_nand_writer_guard import CHILD,WRITER
from audit_v283_nand_early_guard import classify as prior
from audit_v280_nand_r3_producer import trace_source
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

def classify(words:list[int])->str:
    rows=prior(words)
    if len(rows)!=2:
        raise ValueError("guards")
    # V283 verified original first branch at byte offset 88,
    # immediately after cmpwi r3, 0 at offset 84.
    index=88//4
    w=words[index-1]
    if not (w>>26==11 and ((w>>23)&7)==0
            and ((w>>16)&31)==3 and (w&0xffff)==0):
        raise ValueError("early_comparison")
    source=trace_source(words,index-1,3)
    return (
        f"V284_NAND_EARLY child=8052fa60 "
        f"compare_offset=84 branch_offset=88 skip_target=188 "
        f"source={source['kind']} source_offset={source['offset']} "
        f"target={source['target']:08x} tracked={source['tracked']} "
        f"copies={source['copies']} width={source['width']} "
        f"base={source['base']} disp={source['disp']}"
    )

def audit(data:bytes)->str:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000 or WRITER not in funcs:
        raise ValueError("symbols")
    n=funcs.get(CHILD,0)
    if n<32 or n>32768 or n&3:raise ValueError("geometry")
    return classify(read_words(data,CHILD,n//4))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: result=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V284_EARLY_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V284_EARLY_AUDIT verified=1")
    print(result)
    return 0

if __name__=="__main__":
    sys.exit(main())
