#!/usr/bin/env python3
"""Original memory protection init with translated MEM1/MEM2 BAT trampolines."""
import argparse,struct
from pathlib import Path
from make_start_to_dsp_return_v64 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections,data_at
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x805208F4
MEMORY=0x805276D4
NODE=0x8060D030
RANGES=((0x804B79DC,0x804B79EC),(0x805270C4,0x80527218),
        (0x80527550,0x80527688),(MEMORY,0x805277A0))
GUARDS=(0x80527040,0x8052707C,0x80527218,0x805272EC,0x80527394,0x80527468)
EDGES=((PREV_STOP,0x804B79DC),(0x805208E0,0x804B79E4),(0x805208F0,MEMORY),
       (0x80527714,0x8052693C),(0x80527760,0x80527B4C),(0x8052776C,0x80527568),
       (0x80527774,0x805269BC),(0x805275CC,0x80527550),(0x805275FC,0x80527550))
def make(owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V65 original memory protection call edge changed")
    for pc in (0x80527140,0x80527214,0x80527564):
        if (word(text_at(raw,pc,4),0)>>1)&1023!=50:raise ValueError("original BAT trampoline rfi changed")
    def install(lo,body,expected,code):
        hits=[(b,c) for b,c in text if b<=lo and lo+len(body)<=b+len(c)]
        if len(hits)!=1:raise ValueError(f"V65 private fixture range {code} not mapped")
        b,c=hits[0];at=lo-b
        if c[at:at+len(body)]!=expected:raise ValueError(f"V65 private fixture range {code} overlap")
        c[at:at+len(body)]=body
    for i,(lo,hi) in enumerate(RANGES):install(lo,text_at(raw,lo,hi-lo),struct.pack(">I",NOP)*((hi-lo)//4),i)
    for i,addr in enumerate(GUARDS):install(addr,struct.pack(">II",SC,BLR),struct.pack(">II",NOP,NOP),4+i)
    n=STOP-PREV_STOP
    install(PREV_STOP,text_at(raw,PREV_STOP,n)+struct.pack(">II",SC,BLR),
            struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(n//4),10)
    node=data_at(raw,NODE,16)
    if word(node,0)!=GUARDS[0] or word(node,4)!=127 or node[8:]!=bytes(8):
        raise ValueError("V65 original shutdown registration data changed")
    data=data_sections(old)
    if len(data)!=8:raise ValueError("V65 inherited data count differs")
    data.append((NODE,node));out=bytearray(old[:256])
    for is_data,sections in ((False,text),(True,data)):
        for i,(b,c) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),b),((0xac if is_data else 0x90),len(c))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(c);out.extend(b"\0"*((-len(out))%4))
    if out[0xe0:0x100]!=old[0xe0:0x100] or word(out,0xe0)!=START:raise ValueError("V65 original entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V65 original memory protection and BAT trampoline fixture")
