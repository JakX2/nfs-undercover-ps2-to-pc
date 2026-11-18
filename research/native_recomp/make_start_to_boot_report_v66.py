#!/usr/bin/env python3
"""Restore original boot information and native console-type jump-table selection."""
import argparse,struct
from pathlib import Path
from make_start_to_memory_protect_v65 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections,data_at
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x80520908
LOW=0x8051FD44
RANGES=((LOW,0x8051FFC8),(0x805203C4,0x80520670),(0x8052701C,0x80527040),
        (0x80521D18,0x80521D28),(0x80521D30,0x80521D3C))
DATA=((0x8060B7A8,600),(0x8070A898,24))
EDGES=((PREV_STOP,0x805203C4),(0x80520904,0x80522F00),(0x8052040C,LOW),
       (0x8051FEC4,0x8052701C),(0x805205F8,0x80527034),(0x80520600,0x80527028),
       (0x80520618,0x80521D18),(0x80520620,0x80521D30),
       (0x80520638,0x80521D20),(0x80520640,0x80521D38))
def make(owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V66 original boot report call edge changed")
    base,body=text[1]
    if base!=0x80520670 or any(i!=1 and b<base and LOW<b+len(c) for i,(b,c) in enumerate(text)):
        raise ValueError("V66 original boot report extension overlaps inherited text")
    text[1]=(LOW,bytearray(struct.pack(">I",NOP)*((base-LOW)//4))+body)
    def install(lo,body,expected):
        hits=[(b,c) for b,c in text if b<=lo and lo+len(body)<=b+len(c)]
        if len(hits)!=1:raise ValueError("V66 original report span unmapped")
        b,c=hits[0];at=lo-b
        if c[at:at+len(body)]!=expected:raise ValueError("V66 report overwrites inherited text")
        c[at:at+len(body)]=body
    for lo,hi in RANGES:
        original=text_at(raw,lo,hi-lo)
        if word(original,len(original)-4)!=BLR:raise ValueError("V66 original report helper return changed")
        install(lo,original,struct.pack(">I",NOP)*((hi-lo)//4))
    n=STOP-PREV_STOP
    install(PREV_STOP,text_at(raw,PREV_STOP,n)+struct.pack(">II",SC,BLR),
            struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(n//4))
    data=data_sections(old)
    if len(data)!=9:raise ValueError("V66 inherited data count changed")
    data.extend((a,data_at(raw,a,n)) for a,n in DATA)
    report=data[-2][1];small=data[-1][1]
    targets={word(report,496+i*4) for i in range(26)}
    if len(targets)!=7 or any(t<0x805204EC or t>0x8052054C or t&3 for t in targets):
        raise ValueError("V66 original console jump table geometry changed")
    if word(small,0)!=DATA[0][0]:raise ValueError("V66 original version pointer differs")
    out=bytearray(old[:256])
    for is_data,sections in ((False,text),(True,data)):
        for i,(b,c) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),b),((0xac if is_data else 0x90),len(c))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(c);out.extend(b"\0"*((-len(out))%4))
    if out[0xe0:0x100]!=old[0xe0:0x100] or word(out,0xe0)!=START:raise ValueError("V66 original entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V66 original boot-report and console selection fixture")
