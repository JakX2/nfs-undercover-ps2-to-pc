#!/usr/bin/env python3
"""Exact original thread code and callback-data oracle."""
import argparse,struct
from pathlib import Path
from make_start_to_sram_return_v60 import make as previous,STOP as PREV_STOP
from make_start_to_thread_return_v61 import RANGES,CALLBACK_PTR
from make_start_to_si_sampling_v58 import data_at
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    expected=bytearray(old)
    def locate(pc):
        hits=[(i,b,c) for i,(b,c) in enumerate(text) if b<=pc and pc+4<=b+len(c)]
        if len(hits)!=1:raise ValueError("thread code geometry unmapped")
        i,b,c=hits[0];return word(old,i*4)+pc-b,word(c,pc-b)
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):
            at,was=locate(pc)
            if was!=NOP:raise ValueError("thread original code overwrote prior milestone")
            expected[at:at+4]=text_at(raw,pc,4)
    for pc,op,was in ((PREV_STOP+4,SC,BLR),(PREV_STOP+8,BLR,NOP)):
        at,before=locate(pc)
        if before!=was:raise ValueError("thread OSInit guard geometry changed")
        expected[at:at+4]=struct.pack(">I",op)
    at,before=locate(PREV_STOP)
    if before!=SC:raise ValueError("V60 stop changed")
    expected[at:at+4]=text_at(raw,PREV_STOP,4)
    for k,v in ((0x1c,len(old)),(0x64,CALLBACK_PTR),(0xac,4)):
        if word(old,k+24):raise ValueError("thread initialized data slot already present")
        struct.pack_into(">I",expected,k+24,v)
    expected.extend(data_at(raw,CALLBACK_PTR,4))
    if expected!=actual:raise ValueError("thread original span, data or prior code changed")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path)
    a=p.parse_args();verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact V61 original thread/context/stack code and callback pointer")
