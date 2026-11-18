#!/usr/bin/env python3
"""Owner-private DSP bootstrap staging; restores original DCFlushRange and sc."""
import argparse,struct
from pathlib import Path
from make_start_to_audio_reset_v62 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections,data_at
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x80522044
GETHI=0x80521D28
FLUSH=0x805222C0
MICROCODE=0x8060BCC8
RANGES=((GETHI,GETHI+8),(PREV_STOP,STOP),(FLUSH,FLUSH+48))
EDGES=((PREV_STOP,GETHI),(0x80522020,0x80004338),(0x80522034,0x80004338),(0x80522040,FLUSH))
def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V63 original DSP staging call graph changed")
    if word(text_at(raw,FLUSH+40,4),0)!=SC or word(text_at(raw,FLUSH+44,4),0)!=BLR:
        raise ValueError("V63 genuine DCFlushRange syscall/return changed")
    text,_=sections_of(old)
    b,c=text[1];end=STOP+8
    if b+len(c)!=PREV_STOP+8 or end>0x80522280:raise ValueError("V63 previous audio extent changed")
    c.extend(struct.pack(">I",NOP)*((end-b-len(c))//4))
    def install(lo,hi,original):
        hits=[(b,c) for b,c in text if b<=lo and hi<=b+len(c)]
        if len(hits)!=1:raise ValueError("V63 original DSP staging code range unmapped")
        b,c=hits[0];at=lo-b
        expected=bytearray(struct.pack(">I",NOP)*((hi-lo)//4))
        if lo==PREV_STOP:expected[:8]=struct.pack(">II",SC,BLR)
        if c[at:at+hi-lo]!=expected:raise ValueError("V63 original DSP staging overlaps verified code")
        c[at:at+hi-lo]=original
    for lo,hi in RANGES:install(lo,hi,text_at(raw,lo,hi-lo))
    install(STOP,STOP+8,struct.pack(">II",SC,BLR))
    data=data_sections(old)
    if len(data)!=7:raise ValueError("V63 unexpected inherited data count")
    data.append((MICROCODE,data_at(raw,MICROCODE,128)))
    out=bytearray(old[:256])
    for is_data,sections in ((False,text),(True,data)):
        for i,(base,body) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),base),((0xac if is_data else 0x90),len(body))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(body);out.extend(b"\0"*((-len(out))%4))
    if out[0xe0:0x100]!=old[0xe0:0x100] or word(out,0xe0)!=START:
        raise ValueError("V63 original DOL entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V63 original DSP bootstrap staging and syscall fixture")
