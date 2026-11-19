#!/usr/bin/env python3
"""V125 original-free generator instrumentation for invalid PPC BL callsites."""
from pathlib import Path
import argparse
from derive_v104_sc_async_submit_generator import derive as previous

OLD='''uint32_t branch(uint32_t ins,uint32_t pc){
 require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");'''
NEW='''uint32_t branch(uint32_t ins,uint32_t pc){
 if((ins>>26)!=18u||(ins&3u)!=1u){
   std::cout<<"V125_BAD_BRANCH site="<<std::hex<<pc<<std::dec
            <<" major="<<(ins>>26)<<" link="<<((ins&1u)!=0u)
            <<" absolute="<<((ins&2u)!=0u)<<std::endl;
 }
 require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");'''

def derive(source):
    source=previous(source)
    if source.count(OLD)!=1:
        raise ValueError("V125 generator expected-BL assertion anchor ambiguous")
    source=source.replace(OLD,NEW,1)
    old_loop="   for(uint32_t pc:{0x8051e3dcu,0x8051e518u,0x8051e5bcu}){"
    restored='''   require(funcs.count(0x8051e5bcu)==1u,"V125 authenticated SC helper missing");
   const auto& sc_helper=funcs.at(0x8051e5bcu).instructions;
   require(sc_helper.size()>=2u&&sc_helper.front().address==0x8051e5bcu&&
           sc_helper.back().address<0x8051e71cu&&
           sc_helper.back().opcode==0x4e800020u,
           "V125 original SC helper translated geometry differs");
   for(uint32_t pc:{0x8051e3dcu,0x8051e518u}){'''
    if source.count(old_loop)!=1:
        raise ValueError("V125 authentic SC helper guard insertion anchor ambiguous")
    return source.replace(old_loop,restored,1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
