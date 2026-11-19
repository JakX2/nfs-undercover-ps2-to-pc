#!/usr/bin/env python3
"""Classify V125 exception messages without emitting game-derived text or addresses."""
import argparse
from pathlib import Path
import re

ERROR=re.compile(r"what\(\):\s*([^\r\n]+)")
PATTERNS={
 "missing":r"missing|unimplemented|unsupported|unknown|unresolved|not found|not implemented",
 "memory":r"out of bounds|out.of.range|invalid (?:address|memory|access)|unmapped|segmentation",
 "limit":r"instruction limit|timed out|timeout|execution budget|maximum instructions",
 "stop":r"ExceptionStop|exact test-only syscall",
 "lookup":r"unordered_map::at|map::at|bad_function_call|vector::_M_range_check|out_of_range",
 "dispatch":r"dispatch|jump target|call target|function pointer|indirect branch",
 "state":r"invalid (?:state|context|thread)|illegal (?:instruction|register)|assertion",
}
TYPES={
 "runtime":r"instance of ['\"]std::runtime_error['\"]",
 "range":r"instance of ['\"]std::out_of_range['\"]",
 "logic":r"instance of ['\"]std::logic_error['\"]",
}
def classify(log:str)->dict[str,int]:
    messages=ERROR.findall(log)
    message=messages[-1] if messages else ""
    out={"exception":int(bool(messages) or "terminate called after throwing" in log),
         "fault":int(bool(re.search(r"Segmentation fault|SIGSEGV|AddressSanitizer|UndefinedBehaviorSanitizer",log,re.IGNORECASE)))}
    out.update({k:int(bool(re.search(pattern,message,re.IGNORECASE))) for k,pattern in PATTERNS.items()})
    out.update({k:int(bool(re.search(pattern,log))) for k,pattern in TYPES.items()})
    return out
def format_report(log:str)->str:
    items=classify(log)
    return "V125_RUNTIME_SHAPE "+" ".join(f"{key}={value}" for key,value in items.items())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    a=p.parse_args()
    print(format_report(a.private_native_log.read_text(encoding="utf-8",errors="replace")))
if __name__=="__main__":
    main()
