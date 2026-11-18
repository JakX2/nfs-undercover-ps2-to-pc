#!/usr/bin/env python3
"""Independent verification that only the bounded V69 IPC code changed."""
import argparse,struct
from pathlib import Path
from make_start_to_irq_enable_v68 import make as previous,STOP as OLD
from make_start_to_ipc_client_v69 import SPANS,LOW,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    base,body=expected[1];expected[1]=(LOW,bytearray(struct.pack(">I",NOP)*((base-LOW)//4))+body)
    def put(pc,before,after):
        matches=[(b,c) for b,c in expected if b<=pc and pc+len(after)<=b+len(c)]
        if len(matches)!=1:raise ValueError("V69 geometry missing")
        b,c=matches[0];at=pc-b
        if c[at:at+len(after)]!=before:raise ValueError("V69 inherited code changed")
        c[at:at+len(after)]=after
    for pc,size in SPANS:put(pc,struct.pack(">I",NOP)*(size//4),text_at(raw,pc,size))
    put(OLD,struct.pack(">III",SC,BLR,NOP),text_at(raw,OLD,4)+struct.pack(">II",SC,BLR))
    if got!=expected or data_sections(actual)!=data_sections(old) or actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V69 unexpected fixture change")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: exact V69 original IPC geometry")
