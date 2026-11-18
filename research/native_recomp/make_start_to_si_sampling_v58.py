#!/usr/bin/env python3
"""Private original SIInit through sampling setup, polling and IRQ enable.
Owner code/data are extracted only from the SHA-pinned original DOL.
Controller discovery remains a deliberate test boundary.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_return_v57 import make as previous,STOP as PREV_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
SI=0x80532080
STOP=0x80532108
REPEAT_STOP=0x80532130
OS_STOP=0x805208CC
RATE=0x80532D6C
RATE_END=0x80532E44
XY=0x8053238C
XY_END=0x805323E8
TV=0x80536BF8
TV_END=0x80536C58
DATA_RANGES=((0x8070AA70,4),(0x80619A60,0x88),(0x8061A890,36))
EDGES=((PREV_STOP,SI),(0x8053209C,0x80521018),(0x805320D0,RATE),
       (0x805320FC,0x805265F8),(0x80532104,0x805269BC),
       (0x80532DA8,TV),(0x80532E1C,XY),(0x805323A8,0x805265AC),
       (0x80536C08,0x805265AC),(0x80536C3C,0x805265D4))
def data_at(raw,addr,size):
    hits=[]
    for i in range(11):
        off,base,n=(word(raw,k+4*i) for k in (0x1c,0x64,0xac))
        if base<=addr and addr+size<=base+n:
            at=off+addr-base
            if at<256 or at+size>len(raw):raise ValueError("invalid original SI data span")
            hits.append(raw[at:at+size])
    if len(hits)!=1:raise ValueError("SI data span not uniquely mapped")
    return hits[0]

def data_sections(raw):
    data=[]
    for i in range(11):
        off,base,n=(word(raw,k+4*i) for k in (0x1c,0x64,0xac))
        if n:
            if off<256 or off+n>len(raw):raise ValueError("invalid inherited data span")
            data.append((base,raw[off:off+n]))
    return data

def make(owner:Path)->bytes:
    old=previous(owner);raw=owner.read_bytes()
    for site,target in EDGES:
        if call_target(text_at(raw,site,4),site,site)!=target:
            raise ValueError("original SI sampling dependency changed")
    for lo,hi in ((RATE,RATE_END),(XY,XY_END),(TV,TV_END)):
        if word(text_at(raw,hi-4,4),0)!=BLR:raise ValueError("original SI helper return missing")
    table=data_at(raw,0x8061A890,36)
    if any(not TV<=word(table,i)<TV_END for i in range(0,len(table),4)):
        raise ValueError("original TV dispatch table target outside function")
    text,_=sections_of(old)
    data=data_sections(old)
    if len(data)!=3 or len(text)!=7:raise ValueError("V57 segment count changed")
    base,cache=text[5]
    # V25 already reserved this section through the far-away register
    # save/restore thunks. The SI span must reuse its existing guarded NOPs.
    if base!=0x80522540 or not base<=SI<TV_END<=base+len(cache):
        raise ValueError("original SI span outside inherited cache/IPC/save section")
    if any(i!=5 and b<TV_END and b+len(c)>SI
           for i,(b,c) in enumerate(text)):
        raise ValueError("SI text overlaps other original segment")
    def place(addr,body):
        at=addr-base
        if at<0 or at+len(body)>len(cache) or cache[at:at+len(body)]!=struct.pack(">I",NOP)*(len(body)//4):
            raise ValueError("SI restoration would overwrite prior text")
        cache[at:at+len(body)]=body
    place(SI,text_at(raw,SI,STOP-SI))
    place(STOP,struct.pack(">II",SC,BLR))
    place(REPEAT_STOP,struct.pack(">II",SC,BLR))
    for lo,hi in ((RATE,RATE_END),(XY,XY_END),(TV,TV_END)):
        place(lo,text_at(raw,lo,hi-lo))
    text[5]=(base,cache)
    b,code=text[1];at=PREV_STOP-b
    if code[at:at+12]!=struct.pack(">III",SC,BLR,NOP):
        raise ValueError("inherited EXI return stop changed")
    code[at:at+12]=text_at(raw,PREV_STOP,4)+struct.pack(">II",SC,BLR)
    text[1]=(b,code)
    data.extend((a,data_at(raw,a,n)) for a,n in DATA_RANGES)
    out=bytearray(old[:256])
    for i,(guest,blob) in enumerate(text):
        off=len(out)
        for h,v in ((0,off),(0x48,guest),(0x90,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob);out.extend(b"\0"*((-len(out))%4))
    for i,(guest,blob) in enumerate(data):
        off=len(out)
        for h,v in ((0x1c,off),(0x64,guest),(0xac,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob);out.extend(b"\0"*((-len(out))%4))
    if word(out,0xe0)!=START:raise ValueError("V58 changed original entry")
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path)
    a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing original overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: private V58 original SI sampling/IRQ fixture")
