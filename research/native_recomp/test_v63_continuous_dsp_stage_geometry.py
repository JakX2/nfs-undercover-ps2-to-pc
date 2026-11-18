#!/usr/bin/env python3
"""Independent exact original original-code/data geometry, including genuine sc."""
import argparse,struct
from pathlib import Path
from make_start_to_audio_reset_v62 import make as previous,STOP as PREV_STOP
from make_start_to_dsp_stage_v63 import RANGES,STOP,MICROCODE
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_at,data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes();expected,_=sections_of(old);actual_text,_=sections_of(actual)
    base,body=expected[1]
    if base+len(body)!=PREV_STOP+8:raise ValueError("V63 previous stop extent changed")
    body.extend(struct.pack(">I",NOP)*((STOP+8-base-len(body))//4))
    def setword(pc,was,now):
        hits=[(b,c) for b,c in expected if b<=pc and pc+4<=b+len(c)]
        if len(hits)!=1:raise ValueError("V63 geometry unmapped")
        b,c=hits[0];at=pc-b
        if word(c,at)!=was:raise ValueError("V63 altered previous code")
        c[at:at+4]=now
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):
            was=SC if pc==PREV_STOP else BLR if pc==PREV_STOP+4 else NOP
            setword(pc,was,text_at(raw,pc,4))
    setword(STOP,NOP,struct.pack(">I",SC));setword(STOP+4,NOP,struct.pack(">I",BLR))
    data=data_sections(old)+[(MICROCODE,data_at(raw,MICROCODE,128))]
    if expected!=actual_text or data!=data_sections(actual) or actual[0xe0:0x100]!=old[0xe0:0x100]:
        raise ValueError("V63 code or initialized data changed")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: V63 exact original DSP data and code geometry")
