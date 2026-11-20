#!/usr/bin/env python3
"""V133 inspect guest SDA byte at the original Wii SC retry decision, read-only."""
import argparse
from pathlib import Path
from derive_v131_retry_state_harness import derive as previous
OLD='''     std::cout<<"V131_RETRY_STATE pc="'''
NEW='''     const uint32_t v133_sda=ctx.gpr[13]-3176u;
     const bool v133_mapped=ctx.mmu.get_ptr(v133_sda)!=nullptr;
     const uint32_t v133_byte=v133_mapped?uint32_t(ctx.mmu.read8(v133_sda)):256u;
     std::cout<<"V133_STATUS_BYTE mapped="<<v133_mapped
              <<" value="<<v133_byte<<" r3="<<ctx.gpr[3]
              <<" eq="<<ctx.cr[0].eq<<std::endl;
     check(v133_mapped,"V133 original Wii SDA byte is not mapped");
     std::cout<<"V131_RETRY_STATE pc="'''
def derive(source):
    s=previous(source)
    if s.count(OLD)!=1:raise ValueError("V133 original-free trace anchor differs")
    return s.replace(OLD,NEW,1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as o:o.write(derive(a.source.read_text(encoding="utf-8")))
