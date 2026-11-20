#!/usr/bin/env python3
"""V128 assert complete original function and inherited OSInit BL edge."""
import argparse
from pathlib import Path
from derive_v127_osinit_first_bl_generator import derive as previous

OLD=" const auto& os=funcs.at(OSINIT).instructions;"
NEW=''' const auto& os=funcs.at(OSINIT).instructions;
 if(owner){
   require(funcs.count(0x8052f830u)==1u,"V128 original post-OSInit helper missing");
   const auto& f128=funcs.at(0x8052f830u).instructions;
   require(f128.size()==71u&&f128.front().address==0x8052f830u&&
           f128.back().address==0x8052f948u&&f128.back().opcode==0x4e800020u,
           "V128 original 71-instruction function geometry differs");
   const auto it128=std::find_if(os.begin(),os.end(),[](const auto& ins){
      return ins.address==0x8052096cu;
   });
   require(it128!=os.end()&&branch(it128->opcode,0x8052096cu)==0x8052f830u,
           "V128 original OSInit call target differs");
 }
'''

def derive(source):
    s=previous(source)
    if s.count(OLD)!=1:
        raise ValueError("V128 original-free analyzer anchor differs")
    return s.replace(OLD,NEW,1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
