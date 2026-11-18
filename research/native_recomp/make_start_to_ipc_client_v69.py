#!/usr/bin/env python3
"""V69 private continuation: original IPCCltInit and all nine direct dependencies."""
import argparse,struct
from pathlib import Path
from make_start_to_irq_enable_v68 import make as previous,STOP as OLD,replace
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

ROOT=0x805194c4
LOW=0x80518fc8
STOP=OLD+4
SPANS=((LOW,0x4c),(0x8051906c,0x10),(0x8051907c,8),(0x80519084,8),(0x8051908c,8),
       (ROOT,0xb4),(0x8051aa04,0x130),(0x8051af28,0xb8),(0x8052ae70,8),(0x8052ae78,8))
EDGES=((OLD,ROOT),(0x805194f4,LOW),(0x805194f8,0x80519084),(0x80519504,0x8051907c),
       (0x80519520,0x8051aa04),(0x8051952c,0x8051908c),(0x8051953c,0x805265f8),
       (0x80519544,0x805269bc),(0x80519550,0x8051906c),(0x80519554,0x8051af28),
       (0x80518fe0,0x8052ae70),(0x80518fe8,0x8052ae78),(0x8051aa28,0x805265ac),(0x8051ab10,0x805265d4))

def make(owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    for site,target in EDGES:
        if call_target(text_at(raw,site,4),site,site)!=target:raise ValueError("V69 original IPC edge changed")
    base,code=text[1]
    if base!=0x8051fd44 or any(i!=1 and b<base and LOW<b+len(c) for i,(b,c) in enumerate(text)):
        raise ValueError("V69 IPC text extension overlaps earlier text")
    text[1]=(LOW,bytearray(struct.pack(">I",NOP)*((base-LOW)//4))+code)
    for pc,size in SPANS:
        blob=text_at(raw,pc,size)
        if word(blob,size-4)!=BLR:raise ValueError("V69 original IPC function return differs")
        hits=[(b,c) for b,c in text if b<=pc and pc+size<=b+len(c)]
        if len(hits)!=1:raise ValueError("V69 IPC text not uniquely mapped")
        b,c=hits[0];at=pc-b
        if c[at:at+size]!=struct.pack(">I",NOP)*(size//4):raise ValueError("V69 original IPC overlaps previous code")
        c[at:at+size]=blob
    out=bytearray(old[:256])
    for is_data,sections in ((False,text),(True,data_sections(old))):
        for i,(b,c) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),b),((0xac if is_data else 0x90),len(c))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(c);out.extend(b"\0"*((-len(out))%4))
    replace(out,OLD,struct.pack(">III",SC,BLR,NOP),text_at(raw,OLD,4)+struct.pack(">II",SC,BLR))
    if out[0xe0:0x100]!=old[0xe0:0x100]:raise ValueError("V69 original entry changed")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    data=make(a.owner)
    with a.output.open("xb") as f:f.write(data)
    print("PASS: V69 private original IPC client fixture")
