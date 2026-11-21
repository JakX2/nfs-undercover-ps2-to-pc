#!/usr/bin/env python3
"""V225 add the original indirect _isfsFuncCb as an AOT analyzer root.

The reduced NWiiRecomp owner-original fixture discovers most functions by
direct branch traversal. IpcReplyHandler invokes _isfsFuncCb via bctrl,
which may not be discovered as a root. Extend analysis ONLY; never
rewrite PowerPC instructions, guest registers, request bytes or callbacks.
"""
import argparse
from pathlib import Path
from derive_v128_next_function_generator import derive as previous

OLD='0x80526a3cu,0x80519318u,0x80529940u,0x80529718u,0x805229b4u});'
NEW='0x80526a3cu,0x80519318u,0x80529940u,0x80529718u,0x805229b4u,0x804f0e04u});'
ROOT_GUARD=''' const auto& funcs=analyzer.get_functions();'''
ASSERT=''' const auto& funcs=analyzer.get_functions();
 if(owner){
   const bool analyzed=funcs.count(0x804f0e04u)==1u;
   std::cout<<"V225_CB_ANALYZER rooted=1 analyzed="<<analyzed<<std::endl;
   require(analyzed,"V225 original indirect callback was not translated into AOT function");
 }'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(ROOT_GUARD)!=1:
        raise ValueError("V225 original analyzed root list or function-list seam differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(ROOT_GUARD,ASSERT,1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
