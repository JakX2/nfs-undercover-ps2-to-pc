#!/usr/bin/env python3
"""V266 owner-original retry comparator audit; no proprietary code output."""
import argparse
from pathlib import Path
import sys
from audit_v265_retry_edge import audit as prior
from audit_v264_osinit_retry_elf import CALLSITE, read_words
from make_private_elf_symbol_map import parse_functions
from ppc_retry_condition import classify_condition, sanitized

def inspect(data:bytes)->dict[str,int]:
    old=prior(data)   # verifies full SHA, owner symbol geometry and BO/BI
    if old["bo"]!=12 or old["bi"]!=2 or old["back_span"]!=8:
        raise ValueError("unverified_edge")
    funcs=parse_functions(data)
    owners=[(pc,size) for pc,size in funcs.items()
            if pc<=CALLSITE<pc+size and 0x80400000<=pc<0x80600000]
    if len(owners)!=1:
        raise ValueError("owner_function")
    start,size=owners[0]
    lo=CALLSITE-24
    hi=CALLSITE+4*65
    if lo<start or hi>start+size:
        raise ValueError("window")
    return classify_condition(lo,read_words(data,lo,(hi-lo)//4),CALLSITE)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    args=p.parse_args()
    try:
        result=inspect(args.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V266_CONDITION_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V266_CONDITION_AUDIT verified=1")
    print(sanitized(result))
    return 0

if __name__=="__main__":
    sys.exit(main())
