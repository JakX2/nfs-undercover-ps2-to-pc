#!/usr/bin/env python3
"""V43 owner-private continuous Wii __start -> native __OSInitAlarm.

The original owner Wii DOL alone provides PPC words. Retains the V42
native syscall-vector checks and extends the executable image with the
authentic alarm, handler-accessor and shutdown-list registration functions.
The next unrelated OSInit service remains a synthetic guarded stop.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_syscall_v42 import make as make_v42,OSINIT
from make_start_to_epilogue_v41 import sections_of
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import SC,BLR,NOP
from make_alarm_v47 import original_text,call_target,ALARM,GET,SET,SHUTDOWN

OLD_STOP=0x805208B0
STOP=0x805208B4
START=0x8000403C
CACHE=0x80522540

def make(owner:Path)->bytes:
    inherited=make_v42(owner) # owner SHA and 41 independent original checkpoints
    raw=owner.read_bytes()
    text,data=sections_of(inherited)
    idx=[i for i,(base,code) in enumerate(text) if base==OSINIT]
    if len(idx)!=1: raise ValueError("V43 original OSInit section missing")
    osidx=idx[0]
    guest,os=text[osidx]
    at=OLD_STOP-guest
    if os[at:at+8]!=struct.pack(">II",SC,BLR) or word(os,at+8)!=NOP:
        raise ValueError("V42 syscall-to-alarm stop changed")
    call=original_text(raw,OLD_STOP,4)
    if call_target(call,OLD_STOP,OLD_STOP)!=ALARM:
        raise ValueError("original OSInit alarm-call target changed")
    getset=original_text(raw,SET,0x24)
    alarm=original_text(raw,ALARM,0x58)
    shutdown=original_text(raw,SHUTDOWN,0x88)
    if word(alarm,0)!=0x9421FFF0 or word(alarm,len(alarm)-4)!=BLR:
        raise ValueError("original Wii alarm initialization function incomplete")
    if word(getset,0x10)!=BLR or word(getset,0x20)!=BLR:
        raise ValueError("original Wii exception handler accessor returns changed")
    if word(shutdown,len(shutdown)-4)!=BLR or word(alarm,0x30)!=0x38600008:
        raise ValueError("original Wii shutdown registration or handler index changed")
    for site,dest in ((ALARM+0x10,GET),(ALARM+0x38,SET),(ALARM+0x44,SHUTDOWN)):
        if call_target(alarm,site,ALARM)!=dest:
            raise ValueError("original Wii alarm call graph differs from owner DOL")
    # Extend this existing original-code section, avoiding new guest segments.
    size=ALARM+len(alarm)-guest
    if size<len(os) or size>0x1800 or size%4:
        # Existing section can be longer, but cannot omit any alarm code.
        if size>0x1800 or size%4: raise ValueError("alarm source outside OSInit section bound")
    if len(os)<size:
        os.extend(struct.pack(">I",NOP)*((size-len(os))//4))
    set_at=SET-guest
    oldset=os[set_at:set_at+len(getset)]
    if len(oldset)!=len(getset) or word(oldset,0)!=SC or word(oldset,4)!=BLR or oldset[8:]!=struct.pack(">I",NOP)*((len(getset)-8)//4):
        raise ValueError("old guarded Wii exception-handler setter would overlap original code")
    alarm_at=ALARM-guest
    if os[alarm_at:alarm_at+len(alarm)]!=struct.pack(">I",NOP)*(len(alarm)//4):
        raise ValueError("original Wii alarm function overlaps previous native startup")
    os[at:at+4]=call
    os[at+4:at+12]=struct.pack(">II",SC,BLR)
    os[set_at:set_at+len(getset)]=getset
    os[alarm_at:alarm_at+len(alarm)]=alarm
    text[osidx]=(guest,os)
    for i,(base,code) in enumerate(text):
        if i!=osidx and base<guest+len(os) and base+len(code)>guest:
            raise ValueError("V43 extended OSInit overlaps unrelated guest text")

    roots=[i for i,(base,code) in enumerate(text)
           if base<=SHUTDOWN and SHUTDOWN+len(shutdown)<=base+len(code)]
    if len(roots)!=1:
        raise ValueError("original Wii shutdown helper not uniquely mapped")
    idx=roots[0];base,body=text[idx]
    if base!=CACHE: raise ValueError("original Wii shutdown helper section moved")
    offset=SHUTDOWN-base
    if body[offset:offset+len(shutdown)]!=struct.pack(">I",NOP)*(len(shutdown)//4):
        raise ValueError("shutdown-registration PPC overlaps prior continuous code")
    body[offset:offset+len(shutdown)]=shutdown
    text[idx]=(base,body)

    out=bytearray(inherited[:256])
    for i,(base,body) in enumerate(text):
        offset=len(out)
        for h,v in ((0,offset),(0x48,base),(0x90,len(body))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(body)
        out.extend(b"\0"*((-len(out))%4))
    for i,(base,body) in enumerate(data):
        offset=len(out)
        for h,v in ((0x1c,offset),(0x64,base),(0xac,len(body))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(body)
        out.extend(b"\0"*((-len(out))%4))
    if word(out,0xe0)!=START: raise ValueError("V43 original Wii entry point changed")
    return bytes(out)

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("owner_original_dol",type=Path)
    cli.add_argument("private_fixture",type=Path)
    a=cli.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        cli.error("refusing to overwrite owner-private native Wii test DOL")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: private V43 original Wii continuous alarm initializer image built")
