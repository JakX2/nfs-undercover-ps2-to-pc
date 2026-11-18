#!/usr/bin/env python3
"""Original MEM1/MEM2 arena clear, DCZeroRange, DCFlushRange and reset-code query."""
import argparse,struct
from pathlib import Path
from make_start_to_boot_report_v66 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x80520944
GUARD=0x80520920
RANGES=((0x8051FFC8,0x80520388),(0x80521D40,0x80521D48),
        (0x8052234C,0x80522378),(0x805285D0,0x80528600))
EDGES=((0x80520920,0x80556178),(0x8052093C,0x8051FFC8),(0x80520940,0x805201A4),
       (0x8051FFDC,0x805285D0),(0x805201B8,0x805285D0),
       (0x80520080,0x8052234C),(0x8052008C,0x805222C0),
       (0x80520264,0x8052234C),(0x80520270,0x805222C0))
def make(owner):
    old=previous(owner);raw=owner.read_bytes();text,_=sections_of(old)
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V67 original arena call graph changed")
    def install(lo,body,expected,code):
        hits=[(b,c) for b,c in text if b<=lo and lo+len(body)<=b+len(c)]
        if len(hits)!=1:raise ValueError(f"V67 private fixture range {code} not mapped")
        b,c=hits[0];at=lo-b
        if c[at:at+len(body)]!=expected:raise ValueError(f"V67 private fixture range {code} overlap")
        c[at:at+len(body)]=body
    for i,(lo,hi) in enumerate(RANGES):
        original=text_at(raw,lo,hi-lo)
        if word(original,len(original)-4)!=BLR:raise ValueError(f"V67 private fixture range {i} return")
        install(lo,original,struct.pack(">I",NOP)*((hi-lo)//4),i)
    n=STOP-PREV_STOP
    continuation=bytearray(text_at(raw,PREV_STOP,n))
    # The boot record/debug alternate is not part of this cold boot lane.
    struct.pack_into(">I",continuation,GUARD-PREV_STOP,SC)
    install(PREV_STOP,continuation+struct.pack(">II",SC,BLR),
            struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(n//4),4)
    data=data_sections(old)
    if len(data)!=11:raise ValueError("V67 inherited data count changed")
    out=bytearray(old[:256])
    for is_data,sections in ((False,text),(True,data)):
        for i,(b,c) in enumerate(sections):
            for k,v in (((0x1c if is_data else 0),len(out)),((0x64 if is_data else 0x48),b),((0xac if is_data else 0x90),len(c))):
                struct.pack_into(">I",out,k+4*i,v)
            out.extend(c);out.extend(b"\0"*((-len(out))%4))
    if out[0xe0:0x100]!=old[0xe0:0x100] or word(out,0xe0)!=START:raise ValueError("V67 original entry changed")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V67 original MEM1/MEM2 arena clear fixture")
