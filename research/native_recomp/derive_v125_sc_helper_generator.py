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
    return source.replace(OLD,NEW,1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
