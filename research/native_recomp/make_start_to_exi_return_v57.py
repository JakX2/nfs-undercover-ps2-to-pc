#!/usr/bin/env python3
"""V57 privately restore the remaining original EXIInit and absent-card probes.

An authenticated initialized-data word supplies the EXI version pointer.
Original EXIProbe takes the no-card branch; optional card-present timing and
special-device initialization remain explicit failing guards. OSReport is
still a synthetic test callback, not a working guest formatter.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_transaction_v56 import make as previous,STOP as PREV_STOP,PROBE,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

STOP=0x805208C8
EXI_END=0x804EFB80
PROBE_END=0x804EF21C
VERSION=0x80521018
VERSION_END=0x80521028
VERSION_POINTER=0x8070A748
GUARDS=(0x804EF160,0x804EF16C,0x804EFB1C,0x804EFB54)
RANGES=((PREV_STOP,EXI_END),(PROBE,PROBE_END),(VERSION,VERSION_END))
EDGES=((0x804EFAF8,0x804EFD7C),(0x804EFB30,0x804EFD7C),
       (0x804EFADC,PROBE),(0x804EFAE4,PROBE),
       (0x804EFB5C,VERSION),(0x804EF0E0,0x805265AC),
       (0x804EF1F4,0x805265D4),
       (0x804EF160,0x80545254),(0x804EF16C,0x80545254),
       (0x804EFB1C,0x804F02A0),(0x804EFB54,0x804F02A0))

def version_data(raw):
    matches=[]
    for i in range(11):
        off,base,size=(word(raw,k+4*i) for k in (0x1c,0x64,0xac))
        if base<=VERSION_POINTER and VERSION_POINTER+4<=base+size:
            at=off+VERSION_POINTER-base
            if at<256 or at+4>len(raw):raise ValueError("EXI version pointer outside original DOL")
            matches.append(raw[at:at+4])
    if len(matches)!=1 or not (0x80000000<=word(matches[0],0)<0x81800000):
        raise ValueError("original EXI version pointer not uniquely authenticated")
    return matches[0]

def make(owner:Path)->bytes:
    old=previous(owner)
    raw=owner.read_bytes()
    for site,target in EDGES:
        if call_target(text_at(raw,site,4),site,site)!=target:
            raise ValueError("original EXI probe or final call graph changed")
    for end in (EXI_END,PROBE_END):
        if word(text_at(raw,end-4,4),0)!=BLR:
            raise ValueError("original EXI return missing")
    # Unlinked original OSRegisterVersion tail call goes to inherited OSReport.
    op=word(text_at(raw,VERSION_END-4,4),0)
    disp=op&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    if op>>26!=18 or op&3 or VERSION_END-4+disp!=0x80522f00:
        raise ValueError("original EXI version-registration tail branch changed")
    text,data=sections_of(old)
    for lo,hi in RANGES:
        body=bytearray(text_at(raw,lo,hi-lo))
        matches=[(base,code) for base,code in text if base<=lo and hi<=base+len(code)]
        if len(matches)!=1:raise ValueError("V57 original range outside inherited DOL")
        base,code=matches[0];at=lo-base
        expected=struct.pack(">I",NOP)*((hi-lo)//4)
        if lo in (PREV_STOP,PROBE):
            expected=struct.pack(">II",SC,BLR)+expected[8:]
        if code[at:at+len(body)]!=expected:
            raise ValueError("V57 refused overwrite of verified original code")
        for pc in GUARDS:
            if lo<=pc<hi:
                body[pc-lo:pc-lo+4]=struct.pack(">I",SC)
        code[at:at+len(body)]=body
    stop=[(base,code) for base,code in text if base<=STOP and STOP+8<=base+len(code)]
    if len(stop)!=1 or stop[0][1][STOP-stop[0][0]:STOP-stop[0][0]+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V57 inherited OSInit stop missing")
    out=bytearray(old)
    for i,(base,blob) in enumerate(text):
        off=word(old,4*i)
        if word(old,0x90+4*i)!=len(blob):raise ValueError("V57 changed inherited text geometry")
        out[off:off+len(blob)]=blob
    if any(word(old,h+8) for h in (0x1c,0x64,0xac)):
        raise ValueError("V57 extra owner-private data slot unavailable")
    for h,v in ((0x1c,len(out)),(0x64,VERSION_POINTER),(0xac,4)):
        struct.pack_into(">I",out,h+8,v)
    out.extend(version_data(raw))
    if word(out,0xe0)!=START:
        raise ValueError("V57 changed original entry")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path)
    a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():
        p.error("refusing overwrite of owner-private executable")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V57 private original EXIInit return fixture")
