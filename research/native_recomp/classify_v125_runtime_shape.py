#!/usr/bin/env python3
"""Report a bounded, original-free V125 native failure shape. Never show private log text."""
import argparse
from pathlib import Path
import re

PATTERNS={
 "exception":r"what\(\):|terminate called after throwing",
 "fault":r"Segmentation fault|SIGSEGV|AddressSanitizer|UBSan|UndefinedBehaviorSanitizer",
 "missing":r"unimplemented|unsupported|unknown (?:instruction|function|opcode)|missing (?:function|translation)",
 "memory":r"out of bounds|out.of.range|invalid (?:address|memory|access)|unmapped",
 "limit":r"instruction limit|timed out|timeout|execution budget|maximum instructions",
 "stop":r"ExceptionStop|exact test-only syscall",
 "lookup":r"unordered_map::at|map::at|bad_function_call|vector::_M_range_check|out_of_range",
 "dispatch":r"dispatch|jump target|call target|function pointer|indirect branch",
 "state":r"invalid (?:state|context|thread)|illegal (?:instruction|register)|assertion",
}
def classify(log:str)->dict[str,int]:
    return {k:int(bool(re.search(v,log,re.IGNORECASE))) for k,v in PATTERNS.items()}
def format_report(log:str)->str:
    values=classify(log)
    return "V125_RUNTIME_SHAPE "+" ".join(f"{key}={values[key]}" for key in PATTERNS)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    a=p.parse_args()
    print(format_report(a.private_native_log.read_text(encoding="utf-8",errors="replace")))
if __name__=="__main__":
    main()
