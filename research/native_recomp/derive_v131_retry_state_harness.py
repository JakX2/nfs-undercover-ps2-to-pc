#!/usr/bin/env python3
"""V131 observe guest r3 and CR0 after original Wii OSInit retry comparison."""
import argparse
from pathlib import Path
from derive_v130_irq_restore_harness import derive as previous
OLD='''     std::cout<<"V130_NEXT_CALL pc="'''
NEW='''     const bool retry_back=addr==0x8052f830u&&ctx.lr==0x80520970u;
     std::cout<<"V131_RETRY_STATE pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" r3="<<ctx.gpr[3]<<" eq="<<ctx.cr[0].eq
              <<" back="<<retry_back<<std::endl;
     check(retry_back&&ctx.cr[0].eq,"V131 original retry comparison state differs");
     std::cout<<"V130_NEXT_CALL pc="'''
def derive(source):
    s=previous(source)
    if s.count(OLD)!=1:
        raise ValueError("V131 retry guest CR0 observer anchor missing")
    return s.replace(OLD,NEW,1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
