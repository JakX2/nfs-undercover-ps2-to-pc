#!/usr/bin/env python3
"""Compare V68 against the complete prior private fixture independently."""
import argparse,struct
from pathlib import Path
from make_start_to_arena_clear_v67 import make as previous,STOP as OLD
from make_start_to_irq_enable_v68 import ENABLE,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(actual,owner):
    old=previous(owner);src=owner.read_bytes()
    expected,_=sections_of(old);got,_=sections_of(actual)
    def patch(pc,expected_word,new):
        hits=[(b,c) for b,c in expected if b<=pc< b+len(c)]
        if len(hits)!=1:raise ValueError("V68 geometry missing")
        b,c=hits[0];at=pc-b
        if c[at:at+4]!=struct.pack(">I",expected_word):raise ValueError("V68 inherited word differs")
        c[at:at+4]=new
    for pc in range(ENABLE,ENABLE+20,4):patch(pc,NOP,text_at(src,pc,4))
    patch(OLD,SC,text_at(src,OLD,4))
    patch(STOP,BLR,struct.pack(">I",SC))
    patch(STOP+4,NOP,struct.pack(">I",BLR))
    if got!=expected or data_sections(actual)!=data_sections(old) or actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V68 unexpected difference from V67")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact original V68 interrupt-enable geometry")
