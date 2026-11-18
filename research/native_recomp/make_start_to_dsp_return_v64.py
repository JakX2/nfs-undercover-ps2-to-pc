#!/usr/bin/env python3
"""Restore original DSP reset, ARAM DMA, mailbox and audio return."""
import argparse,struct
from pathlib import Path
from make_start_to_dsp_stage_v63 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x805208D8
END=0x805221B4
EDGES=((0x805220C8,0x8052A83C),(0x805220D0,0x8052A83C),
       (0x80522188,0x80521D28),(0x8052219C,0x80004338))
def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V64 original DSP call edge changed")
    body=text_at(raw,PREV_STOP,END-PREV_STOP)
    if word(body,len(body)-4)!=BLR:raise ValueError("V64 original audio epilogue changed")
    text,_=sections_of(old);base,os=text[1]
    if base+len(os)!=PREV_STOP+8 or os[-8:]!=struct.pack(">II",SC,BLR):
        raise ValueError("V64 inherited audio guard differs")
    if word(os,STOP-base)!=SC:raise ValueError("V64 OSInit stop differs")
    os[-8:]=body
    if base+len(os)!=END or END>0x80522280:raise ValueError("V64 audio text overlap")
    out=bytearray(old[:256]);data=data_sections(old)
    if len(data)!=8:raise ValueError("V64 inherited data count changed")
    for is_data,sections in ((False,text),(True,data)):
        for i,(b,c) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),b),((0xac if is_data else 0x90),len(c))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(c);out.extend(b"\0"*((-len(out))%4))
    if out[0xe0:0x100]!=old[0xe0:0x100] or word(out,0xe0)!=START:
        raise ValueError("V64 original entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V64 original DSP handshake and return fixture")
