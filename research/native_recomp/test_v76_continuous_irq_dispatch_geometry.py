#!/usr/bin/env python3
"""Verify original restored code and the sole new IPC checkpoint."""
import argparse,struct
from pathlib import Path
from make_start_to_external_vector_v75 import make as previous,STOP as TRAMPOLINE
from make_start_to_irq_dispatch_v76 import SPANS,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    def put(pc,before,after):
        hits=[(b,c) for b,c in expected if b<=pc and pc+len(after)<=b+len(c)]
        if len(hits)!=1:raise ValueError("V76 geometry missing range")
        b,c=hits[0];i=pc-b
        if c[i:i+len(after)]!=before:raise ValueError("V76 geometry overlap")
        c[i:i+len(after)]=after
    for pc,size in SPANS:
        before=struct.pack(">I",NOP)*(size//4)
        if pc==TRAMPOLINE:before=struct.pack(">II",SC,BLR)+before[8:]
        put(pc,before,text_at(raw,pc,size))
    put(STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    if got!=expected or data_sections(actual)!=data_sections(old) or old[:256]!=actual[:256]:
        raise ValueError("V76 unexpected fixture difference")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: V76 exact private IRQ dispatcher fixture geometry")
