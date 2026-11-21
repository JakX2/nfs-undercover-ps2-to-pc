#!/usr/bin/env python3
"""V232 AOT roots the original NAND open async callback invoked by ISFS.

The original _isfsFuncCb invokes its completion callback via bctrl.
The selected game's nandOpenCallback is not a mandatory direct-branch
target in NWiiRecomp's reduced starting root graph. Add an analysis
root only, preserving all original PowerPC bytes and guest state.
"""
import argparse
from pathlib import Path
from derive_v225_isfs_callback_generator import (
    derive as previous, NEW as PREVIOUS_ROOTS, ASSERT as PREVIOUS_ASSERT,
)
NEW_ROOTS=PREVIOUS_ROOTS.replace("0x804f0e04u});",
                                 "0x804f0e04u,0x8051e06cu});")
INSERT='''   const bool nand=funcs.count(0x8051e06cu)==1u;
   std::cout<<"V232_CB_ANALYZER rooted=1 analyzed="<<nand<<std::endl;
   require(nand,"V232 original NAND open callback missing from AOT translation");'''
def derive(source:str)->str:
    s=previous(source)
    if s.count(PREVIOUS_ROOTS)!=1 or s.count(PREVIOUS_ASSERT)!=1:
        raise ValueError("V232 original V225 AOT callback root seam changed")
    s=s.replace(PREVIOUS_ROOTS,NEW_ROOTS,1)
    s=s.replace(PREVIOUS_ASSERT,PREVIOUS_ASSERT.replace(
        '   require(analyzed,"V225 original indirect callback was not translated into AOT function");',
        '   require(analyzed,"V225 original indirect callback was not translated into AOT function");\n'+INSERT),1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
