#!/usr/bin/env python3
"""Original OS thread initialization, including private initialized callback pointer."""
import argparse,struct
from pathlib import Path
from make_start_to_sram_return_v60 import make as previous,STOP as PREV_STOP,START
from make_start_to_si_sampling_v58 import data_at
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x805208D4
THREAD=0x8052912C
CALLBACK=0x80529128
CLEAR=0x80522AF4
CURRENT=0x805228CC
GETSP=0x80522A8C
CALLBACK_PTR=0x8070A908
RANGES=((CALLBACK,THREAD),(THREAD,0x805293B0),(CLEAR,0x80522B18),
        (CURRENT,0x80522928),(GETSP,0x80522A94))
EDGES=((PREV_STOP,THREAD),(0x8052919C,CLEAR),(0x805291A4,CURRENT),
       (0x805291E4,GETSP),(0x8052938C,CLEAR))
def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("original thread initialization call graph changed")
    if (word(text_at(raw,0x805291DC,4),0)>>1)&1023!=528 or not word(text_at(raw,0x805291DC,4),0)&1:
        raise ValueError("original thread indirect callback instruction changed")
    pointer=data_at(raw,CALLBACK_PTR,4)
    if word(pointer,0)!=CALLBACK:raise ValueError("original thread callback pointer changed")
    text,_=sections_of(old)
    for lo,hi in RANGES:
        hits=[(b,c) for b,c in text if b<=lo and hi<=b+len(c)]
        if len(hits)!=1:raise ValueError("thread original helper range not uniquely mapped")
        b,c=hits[0];at=lo-b
        if c[at:at+hi-lo]!=struct.pack(">I",NOP)*((hi-lo)//4):
            raise ValueError("thread restore overlaps verified original code")
        original=text_at(raw,lo,hi-lo)
        if word(original,len(original)-4)!=BLR:raise ValueError("thread original helper missing return")
        c[at:at+hi-lo]=original
    b,c=text[1];at=PREV_STOP-b
    if c[at:at+12]!=struct.pack(">III",SC,BLR,NOP):raise ValueError("V60 original OSInit stop changed")
    c[at:at+12]=text_at(raw,PREV_STOP,4)+struct.pack(">II",SC,BLR)
    out=bytearray(old)
    for i,(base,body) in enumerate(text):
        off=word(old,4*i)
        if len(body)!=word(old,0x90+4*i):raise ValueError("thread original section geometry changed")
        out[off:off+len(body)]=body
    slot=6
    if any(word(old,k+slot*4) for k in (0x1c,0x64,0xac)):
        raise ValueError("owner thread callback data slot unavailable")
    for k,v in ((0x1c,len(out)),(0x64,CALLBACK_PTR),(0xac,4)):
        struct.pack_into(">I",out,k+slot*4,v)
    out.extend(pointer)
    if word(out,0xe0)!=START:raise ValueError("V61 original entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path)
    p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: private V61 original OS thread init and initialized callback fixture")
