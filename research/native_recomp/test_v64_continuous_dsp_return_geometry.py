#!/usr/bin/env python3
"""Independent exact original audio return and inherited fixture comparison."""
import argparse,struct
from pathlib import Path
from make_start_to_dsp_stage_v63 import make as previous,STOP as PREV_STOP
from make_start_to_dsp_return_v64 import END,STOP
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);got,_=sections_of(actual)
    b,c=expected[1]
    if b+len(c)!=PREV_STOP+8 or c[-8:]!=struct.pack(">II",SC,BLR) or word(c,STOP-b)!=SC:
        raise ValueError("V64 inherited guard differs")
    c[-8:]=text_at(raw,PREV_STOP,END-PREV_STOP)
    if got!=expected or data_sections(old)!=data_sections(actual) or old[0xe0:0x100]!=actual[0xe0:0x100]:
        raise ValueError("V64 original code or inherited data changed")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact original V64 DSP handshake and epilogue")
