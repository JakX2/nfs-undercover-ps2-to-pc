#!/usr/bin/env python3
"""Verify that V75 changes only the nonexecuted handler boundary."""
import argparse,struct
from pathlib import Path
from make_start_to_select_thread_v74 import make as previous
from make_start_to_external_vector_v75 import STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);expected,_=sections_of(old);got,_=sections_of(actual)
    hits=[(b,c) for b,c in expected if b<=STOP and STOP+8<=b+len(c)]
    if len(hits)!=1:raise ValueError("V75 geometry missing handler boundary")
    b,c=hits[0];i=STOP-b
    if c[i:i+8]!=struct.pack(">II",NOP,NOP):raise ValueError("V75 inherited handler boundary modified")
    c[i:i+8]=struct.pack(">II",SC,BLR)
    if got!=expected or data_sections(actual)!=data_sections(old) or old[:256]!=actual[:256]:
        raise ValueError("V75 unexpected fixture difference")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: V75 exact private IRQ handler boundary geometry")
