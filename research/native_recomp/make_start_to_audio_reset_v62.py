#!/usr/bin/env python3
"""Restore original audio bootstrap's timed Hollywood clock/reset helper."""
import argparse,struct
from pathlib import Path
from make_start_to_thread_return_v61 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
AUDIO=0x80521FEC
RESET=0x80521DCC
STOP=0x80522010
OS_STOP=0x805208D8
TBLOW=0x8052A83C
RANGES=((RESET,AUDIO),(AUDIO,STOP),(TBLOW,0x8052A844))
EDGES=((PREV_STOP,AUDIO),(0x8052200C,RESET))+tuple((pc,TBLOW) for pc in
       (0x80521E14,0x80521E28,0x80521EA4,0x80521EB8,0x80521EF0,0x80521F04,
        0x80521F40,0x80521F54,0x80521F90,0x80521FA4))
def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V62 original audio reset call graph changed")
    text,_=sections_of(old)
    def install(lo,body,expected):
        hits=[(b,c) for b,c in text if b<=lo and lo+len(body)<=b+len(c)]
        if len(hits)!=1:raise ValueError("V62 audio reset range not uniquely mapped")
        b,c=hits[0];at=lo-b
        if c[at:at+len(body)]!=expected:raise ValueError("V62 audio reset overlaps original code")
        c[at:at+len(body)]=body
    for lo,hi in RANGES:
        original=text_at(raw,lo,hi-lo)
        if lo!=AUDIO and word(original,len(original)-4)!=BLR:raise ValueError("V62 original reset/time helper lacks return")
        install(lo,original,struct.pack(">I",NOP)*((hi-lo)//4))
    install(STOP,struct.pack(">II",SC,BLR),struct.pack(">II",NOP,NOP))
    install(PREV_STOP,text_at(raw,PREV_STOP,4)+struct.pack(">II",SC,BLR),struct.pack(">III",SC,BLR,NOP))
    out=bytearray(old)
    for i,(base,body) in enumerate(text):
        off=word(old,4*i)
        if len(body)!=word(old,0x90+4*i):raise ValueError("V62 original text geometry changed")
        out[off:off+len(body)]=body
    if out[:256]!=old[:256] or word(out,0xe0)!=START:raise ValueError("V62 original header changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V62 private original audio clock/reset fixture")
