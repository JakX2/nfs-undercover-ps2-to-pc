#!/usr/bin/env python3
"""V127 validate authentic OSInit first BL without retaining the synthetic SC guard."""
import argparse
from pathlib import Path
from derive_v125_sc_helper_generator import derive as previous

EDITS=[
 (""" const auto os_has=[&](uint32_t pc,uint32_t op){
   for(const auto& ins:os)if(ins.address==pc)return ins.opcode==op;
   return false;
 };""",
  """ const auto os_has=[&](uint32_t pc,uint32_t op){
   for(const auto& ins:os)if(ins.address==pc)return ins.opcode==op;
   return false;
 };
 const auto os_original_bl=[&](uint32_t pc){
   for(const auto& ins:os)if(ins.address==pc)
     return (ins.opcode>>26)==18u && (ins.opcode&3u)==1u;
   return false;
 };"""),
 ("os_has(OS_RET_STOP,0x44000002u)","os_original_bl(OS_RET_STOP)"),
 ("os_has(OS_RET_STOP+4u,0x4e800020u)",
  "!os_has(OS_RET_STOP+4u,0x4e800020u)"),
 ("os.size()<=204u","os.size()<=208u")
]
def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if old=="os_has(OS_RET_STOP,0x44000002u)":
            if count!=2:raise ValueError("V127 synthetic OSInit SC guards not exactly two")
            s=s.replace(old,new)
        else:
            if count!=1:raise ValueError("V127 original-free generator anchor differs: "+old[:90]+" count="+str(count))
            s=s.replace(old,new,1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
