#!/usr/bin/env python3
"""V107 read-only owner-data provenance probe at original SC strlen input."""
import argparse
from pathlib import Path
from derive_v104_sc_async_submit_harness import derive as previous
EDITS=[(
    "       if(addr==0x80544ac0u&&ctx.lr==0x8051e740u){",
    """       if(addr==0x80544ac0u&&ctx.lr==0x8051e740u){
         constexpr std::string_view public_sc="/shared2/sys/SYSCONF";
         const uint32_t s=ctx.gpr[3];
         const bool mapped=s&&open71_ram(s,1u);
         const bool guest_empty=mapped&&ctx.mmu.read8(s)==0u;
         bool owner_match=false;
         for(const auto& sec:stm70_owner->sections){
           if(sec.is_bss||sec.is_text||s<sec.address||
              uint64_t(s)+public_sc.size()+1u>uint64_t(sec.address)+sec.data.size())continue;
           bool exact=true;
           for(unsigned i=0;i<public_sc.size();++i)
             exact&=sec.data[s-sec.address+i]==uint8_t(public_sc[i]);
           exact&=sec.data[s-sec.address+public_sc.size()]==0u;
           owner_match|=exact;
         }
         std::cout<<"V107_SC_SOURCE mapped="<<mapped<<" empty="<<guest_empty
                  <<" original_literal="<<owner_match<<std::endl;"""
)]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:raise ValueError("V107 SC source original callsite missing")
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
