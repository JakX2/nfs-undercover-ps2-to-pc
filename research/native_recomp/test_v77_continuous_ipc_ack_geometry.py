#!/usr/bin/env python3
"""Verify the complete exact IPC handler and dependency restoration."""
import argparse,struct
from pathlib import Path
from make_start_to_irq_dispatch_v76 import make as previous,STOP as IPC
from make_start_to_ipc_ack_v77 import SPANS
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    for pc,size in SPANS:
        hits=[(b,c) for b,c in expected if b<=pc and pc+size<=b+len(c)]
        if len(hits)!=1:raise ValueError("V77 geometry missing range")
        b,c=hits[0];i=pc-b
        before=struct.pack(">I",NOP)*(size//4)
        if pc==IPC:before=struct.pack(">II",SC,BLR)+before[8:]
        if c[i:i+size]!=before:raise ValueError("V77 geometry overlap")
        c[i:i+size]=text_at(raw,pc,size)
    if got!=expected or data_sections(actual)!=data_sections(old) or old[:256]!=actual[:256]:
        raise ValueError("V77 unexpected fixture difference")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: V77 exact private IPC handler fixture geometry")
