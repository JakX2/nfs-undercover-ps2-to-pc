#!/usr/bin/env python3
"""Independent original boot report and console classification geometry."""
import argparse,struct
from pathlib import Path
from make_start_to_memory_protect_v65 import make as previous,STOP as PREV_STOP
from make_start_to_boot_report_v66 import RANGES,DATA,LOW,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections,data_at
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    base,body=expected[1];expected[1]=(LOW,bytearray(struct.pack(">I",NOP)*((base-LOW)//4))+body)
    def setword(pc,was,now):
        hits=[(b,c) for b,c in expected if b<=pc and pc+4<=b+len(c)]
        if len(hits)!=1:raise ValueError("V66 geometry unmapped")
        b,c=hits[0];at=pc-b
        if word(c,at)!=was:raise ValueError("V66 changed inherited original text")
        c[at:at+4]=now
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):setword(pc,NOP,text_at(raw,pc,4))
    for pc in range(PREV_STOP,STOP+8,4):
        was=SC if pc==PREV_STOP else BLR if pc==PREV_STOP+4 else NOP
        now=text_at(raw,pc,4) if pc<STOP else struct.pack(">I",SC if pc==STOP else BLR)
        setword(pc,was,now)
    if got!=expected or data_sections(actual)!=data_sections(old)+[(a,data_at(raw,a,n)) for a,n in DATA] or actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V66 original report code or data differs")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact original V66 boot report geometry")
