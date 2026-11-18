#!/usr/bin/env python3
"""Independent expected original spans/padding and owner data comparison."""
import argparse,struct
from pathlib import Path
from make_start_to_exi_return_v57 import make as previous,STOP as PREV_STOP
from make_start_to_si_sampling_v58 import SI,STOP,REPEAT_STOP,RATE,RATE_END,XY,XY_END,TV,TV_END,DATA_RANGES,data_at,data_sections
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes()
    prior,_=sections_of(old);now,_=sections_of(actual)
    if data_sections(actual)!=data_sections(old)+[(a,data_at(raw,a,n)) for a,n in DATA_RANGES]:
        raise ValueError("V58 initialized SI data or inherited payload differs")
    if actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V58 original entry/header tail changed")
    additions={pc:text_at(raw,pc,4) for lo,hi in ((SI,STOP),(RATE,RATE_END),(XY,XY_END),(TV,TV_END))
                 for pc in range(lo,hi,4)}
    for pc in (STOP,REPEAT_STOP):
        additions[pc]=struct.pack(">I",SC);additions[pc+4]=struct.pack(">I",BLR)
    for i,((base,body),(newbase,current)) in enumerate(zip(prior,now)):
        if newbase!=base:raise ValueError("V58 relocated guest text")
        expected=bytearray(body)
        if i==1:
            at=PREV_STOP-base
            if expected[at:at+12]!=struct.pack(">III",SC,BLR,NOP):raise ValueError("V58 old guard changed")
            expected[at:at+12]=text_at(raw,PREV_STOP,4)+struct.pack(">II",SC,BLR)
        if i==5:
            if not base<=SI<TV_END<=base+len(expected):raise ValueError("V58 SI inherited section geometry differs")
            if any(expected[pc-base:pc-base+4]!=struct.pack(">I",NOP) for pc in additions):
                raise ValueError("V58 overlapped old guest code")
            for pc,op in additions.items():expected[pc-base:pc-base+4]=op
        if current!=expected:raise ValueError("V58 original SI or inherited code changed")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path)
    a=p.parse_args();verify(a.fixture.read_bytes(),a.owner)
    print("PASS: V58 private SI code spans, independent data and retained prior originals")
