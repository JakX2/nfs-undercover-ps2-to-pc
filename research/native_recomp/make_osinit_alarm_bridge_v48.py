#!/usr/bin/env python3
"""SHA-pinned owner's private Wii OSInit→alarm startup chain fixture.

Original PowerPC bodies are extracted only from the owner's DOL; distributable
source contains no original Wii program code or generated game C++.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_syscall_bridge_v46 import make as make_v46, be32, OSINIT
from make_alarm_v47 import (original_text, call_target, ALARM, SET, GET,
                            SHUTDOWN, SC, BLR)

NOP=0x60000000
OLD_STOP=0x805208B0
NEW_STOP=0x805208B4
TIME_SECTION=0x805265AC
SYSCALL_SECTION=0x805290A8
END_SECTION=0x8052AE98


def make(owner: Path):
    private = make_v46(owner)  # verifies pinned original SHA and inherited source
    raw=owner.read_bytes()
    segments=[]
    for i in range(7):
        off,a,n=(be32(private,b+4*i) for b in (0,0x48,0x90))
        if off<0x100 or n<=0 or off+n>len(private):
            raise ValueError('inherited original OSInit test image has invalid section')
        segments.append([a,bytearray(private[off:off+n])])
    # The original exception code and the alarm initializer share nearby PCs.
    # The old synthetic SET guard is not reached in V46 normal execution.
    first=segments[0][1]
    assert segments[0][0]==OSINIT
    getset=original_text(raw,SET,0x24)
    alarm=original_text(raw,ALARM,0x58)
    original_call=original_text(raw,OLD_STOP,4)
    if (be32(first,SET-OSINIT)!=SC or
        be32(first,OLD_STOP-OSINIT)!=SC or
        be32(first,OLD_STOP-OSINIT+4)!=BLR or
        be32(first,OLD_STOP-OSINIT+8)!=NOP):
        raise ValueError('inherited OSInit test stops no longer match')
    if call_target(original_call,OLD_STOP,OLD_STOP)!=ALARM:
        raise ValueError('owner original OSInit alarm call differs')
    for site,dest in ((ALARM+0x10,GET),(ALARM+0x38,SET),(ALARM+0x44,SHUTDOWN)):
        if call_target(alarm,site,ALARM)!=dest:
            raise ValueError('owner original alarm helper callgraph differs')
    first[SET-OSINIT:SET-OSINIT+len(getset)]=getset
    first[ALARM-OSINIT:ALARM-OSINIT+len(alarm)]=alarm
    struct.pack_into('>I',first,OLD_STOP-OSINIT,be32(original_call,0))
    struct.pack_into('>II',first,NEW_STOP-OSINIT,SC,BLR)
    # DOL 7 text-section limit: merge existing time and systemcall sections.
    # Only private *unexecuted* gaps are filled with synthetic NOPs. Real PPC
    # shutdown registration is inserted at unchanged original guest PC.
    by_addr={a:body for a,body in segments}
    if [segments[i][0] for i in range(7)] != [OSINIT,SYSCALL_SECTION,TIME_SECTION,
                      0x805450E8,0x80004338,0x804B7920,0x804E50A0]:
        raise ValueError('unexpected V46 private section addresses')
    time=by_addr[TIME_SECTION]
    syscall=by_addr[SYSCALL_SECTION]
    shutdown=original_text(raw,SHUTDOWN,0x88)
    if be32(shutdown,0x84)!=BLR:
        raise ValueError('original shutdown function incomplete')
    gap=SYSCALL_SECTION-TIME_SECTION
    if gap<len(time) or gap%4 or END_SECTION != SYSCALL_SECTION+len(syscall):
        raise ValueError('cannot merge existing test-only code ranges')
    merged=bytearray(NOP.to_bytes(4,'big')*(gap//4))
    merged[0:len(time)]=time
    if SHUTDOWN < TIME_SECTION+len(time) or SHUTDOWN+len(shutdown)>SYSCALL_SECTION:
        raise ValueError('shutdown original function overlaps private test sections')
    merged[SHUTDOWN-TIME_SECTION:SHUTDOWN-TIME_SECTION+len(shutdown)]=shutdown
    merged.extend(syscall)
    out_sections=[segments[0],[TIME_SECTION,merged],segments[3],segments[4],segments[5],segments[6]]
    dataoff,dataaddr,datasize=(be32(private,p) for p in (0x1c,0x64,0xac))
    if dataoff<0x100 or datasize!=0x98 or dataoff+datasize>len(private):
        raise ValueError('original handler template missing')
    data=bytes(private[dataoff:dataoff+datasize])
    result=bytearray(0x100+sum(len(body) for _,body in out_sections)+len(data))
    at=0x100
    for i,(address,body) in enumerate(out_sections):
        for h,value in ((0,at),(0x48,address),(0x90,len(body))):
            struct.pack_into('>I',result,h+4*i,value)
        result[at:at+len(body)]=body
        at+=len(body)
    for h,value in ((0x1c,at),(0x64,dataaddr),(0xac,len(data))):
        struct.pack_into('>I',result,h,value)
    result[at:at+len(data)]=data
    struct.pack_into('>I',result,0xe0,OSINIT)
    return bytes(result)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_dol',type=Path)
    ap.add_argument('private_image',type=Path)
    args=ap.parse_args()
    if args.private_image.exists():ap.error('refusing overwrite of private image')
    args.private_image.write_bytes(make(args.owner_dol))
    print('PASS: V48 private Wii OSInit, syscall and alarm image created')
