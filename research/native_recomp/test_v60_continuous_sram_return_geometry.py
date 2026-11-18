#!/usr/bin/env python3
"""Independent byte-exact original SRAM DMA and no-change path geometry."""
import argparse,struct
from pathlib import Path
from make_start_to_si_return_v59 import make as previous,STOP as PREV_STOP
from make_start_to_sram_return_v60 import RANGES,GUARDS
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    expected=bytearray(old)
    def locate(pc):
        hits=[(i,b,c) for i,(b,c) in enumerate(text) if b<=pc and pc+4<=b+len(c)]
        if len(hits)!=1:raise ValueError("SRAM geometry unmapped")
        i,b,c=hits[0]
        return word(old,i*4)+pc-b,word(c,pc-b)
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):
            at,was=locate(pc)
            if was!=NOP:raise ValueError("V60 overwrote inherited original code")
            expected[at:at+4]=struct.pack(">I",SC) if pc==GUARDS[1] else text_at(raw,pc,4)
    for pc,op,was in ((GUARDS[0],SC,NOP),(GUARDS[0]+4,BLR,NOP),
                     (PREV_STOP+4,SC,BLR),(PREV_STOP+8,BLR,NOP)):
        at,before=locate(pc)
        if before!=was:raise ValueError("V60 boundary geometry changed")
        expected[at:at+4]=struct.pack(">I",op)
    at,before=locate(PREV_STOP)
    if before!=SC:raise ValueError("V60 prior stop changed")
    expected[at:at+4]=text_at(raw,PREV_STOP,4)
    if expected!=actual:raise ValueError("V60 original and guarded byte comparison failed")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path)
    a=p.parse_args();verify(a.fixture.read_bytes(),a.owner)
    print("PASS: independent V60 original SRAM code geometry")
