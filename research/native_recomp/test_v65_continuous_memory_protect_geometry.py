#!/usr/bin/env python3
"""Independent original memory-protection fixture geometry oracle."""
import argparse,struct
from pathlib import Path
from make_start_to_dsp_return_v64 import make as previous,STOP as PREV_STOP
from make_start_to_memory_protect_v65 import RANGES,GUARDS,STOP,NODE
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections,data_at
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    def setword(pc,was,now):
        hits=[(b,c) for b,c in expected if b<=pc and pc+4<=b+len(c)]
        if len(hits)!=1:raise ValueError("V65 geometry unmapped")
        b,c=hits[0];at=pc-b
        if word(c,at)!=was:raise ValueError("V65 changed prior original code")
        c[at:at+4]=now
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):setword(pc,NOP,text_at(raw,pc,4))
    for pc in GUARDS:
        setword(pc,NOP,struct.pack(">I",SC));setword(pc+4,NOP,struct.pack(">I",BLR))
    for pc in range(PREV_STOP,STOP+8,4):
        was=SC if pc==PREV_STOP else BLR if pc==PREV_STOP+4 else NOP
        now=text_at(raw,pc,4) if pc<STOP else struct.pack(">I",SC if pc==STOP else BLR)
        setword(pc,was,now)
    if got!=expected or data_sections(actual)!=data_sections(old)+[(NODE,data_at(raw,NODE,16))] or actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V65 original code/data geometry differs")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact original memory protection and BAT ranges")
