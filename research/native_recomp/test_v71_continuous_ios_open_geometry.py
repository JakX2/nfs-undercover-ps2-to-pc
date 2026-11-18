#!/usr/bin/env python3
"""Independent exact original IOS_Open fixture delta verification."""
import argparse,struct
from pathlib import Path
from make_start_to_stm_v70 import make as previous,OPEN
from make_start_to_ios_open_v71 import SIZE,PROFILE,ALLOC,ALLOC_SIZE,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    def put(pc,before,after):
        matches=[(b,c) for b,c in expected if b<=pc and pc+len(after)<=b+len(c)]
        if len(matches)!=1:raise ValueError("V71 geometry range missing")
        b,c=matches[0];at=pc-b
        if c[at:at+len(after)]!=before:raise ValueError("V71 inherited fixture changed")
        c[at:at+len(after)]=after
    put(OPEN,struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(SIZE//4-2),text_at(raw,OPEN,SIZE))
    put(ALLOC,struct.pack(">I",NOP)*(ALLOC_SIZE//4),text_at(raw,ALLOC,ALLOC_SIZE))
    put(PROFILE,struct.pack(">I",NOP),text_at(raw,PROFILE,4))
    put(STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    if got!=expected or data_sections(actual)!=data_sections(old) or actual[:256]!=old[:256]:
        raise ValueError("V71 unexpected private fixture difference")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: V71 exact private IOS_Open fixture geometry")
