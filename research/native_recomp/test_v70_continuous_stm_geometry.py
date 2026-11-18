#!/usr/bin/env python3
"""Independent byte-for-byte original STM continuation geometry."""
import argparse,struct
from pathlib import Path
from make_start_to_ipc_client_v69 import make as previous,STOP as OLD
from make_start_to_stm_v70 import STM,STM_SIZE,OPEN,IOCTL,OS_STOP,SKIP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    def put(pc,before,after):
        hits=[(b,c) for b,c in expected if b<=pc and pc+len(after)<=b+len(c)]
        if len(hits)!=1:raise ValueError("V70 unique mapped range missing")
        b,c=hits[0];at=pc-b
        if c[at:at+len(after)]!=before:raise ValueError("V70 inherited code differs")
        c[at:at+len(after)]=after
    put(STM,struct.pack(">I",NOP)*(STM_SIZE//4),text_at(raw,STM,STM_SIZE))
    for pc in (OPEN,IOCTL,SKIP):put(pc,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    n=OS_STOP-OLD
    put(OLD,struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(n//4),text_at(raw,OLD,n)+struct.pack(">II",SC,BLR))
    if expected!=got or data_sections(old)!=data_sections(actual) or old[0xe0:0x100]!=actual[0xe0:0x100]:
        raise ValueError("V70 unexpected fixture difference")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner);print("PASS: exact original STM fixture geometry")
