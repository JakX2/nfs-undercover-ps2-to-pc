#!/usr/bin/env python3
"""V55 original Wii EXIGetID cached-ID fast path in continuous __start.

Only the SHA-256-pinned owner's DOL supplies original guest instructions.
The slow, unimplemented device-probe branch stops at a synthetic syscall;
the test injects a cached ID on original function entry to exercise the
unaltered original fast return, not genuine first-boot device detection.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_handlers_v54 import make as make_v54,STOP as OLD_STOP,EXI,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

ID=0x804EFD7C
PREFIX_END=0x804EFDD4
SLOW_STOP=PREFIX_END
EPILOGUE=0x804F0110
EPILOGUE_END=0x804F0128
STOP=0x804EFAB0
SAVE=0x805450F4
REST=0x80545140

def branch_target(op:int,pc:int)->int:
    if op>>26!=18 or (op&3)!=0:
        raise ValueError("expected original non-link relative PowerPC branch")
    disp=op&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    return (pc+disp)&0xffffffff

def verify_original(raw:bytes):
    exi=text_at(raw,EXI,STOP-EXI)
    prefix=text_at(raw,ID,PREFIX_END-ID)
    epilogue=text_at(raw,EPILOGUE,EPILOGUE_END-EPILOGUE)
    if call_target(exi,0x804EFAAC,EXI)!=ID:
        raise ValueError("original EXIInit ID-call target changed")
    if len(prefix)!=0x58 or word(prefix,0)!=0x9421ffc0 or word(prefix,0x4c)>>26!=36:
        raise ValueError("original EXIGetID cached-ID branch/store geometry changed")
    if call_target(prefix,ID+0x10,ID)!=SAVE:
        raise ValueError("original EXIGetID register save helper call changed")
    if branch_target(word(prefix,0x54),ID+0x54)!=EPILOGUE:
        raise ValueError("original EXIGetID cached-return branch target changed")
    if len(epilogue)!=0x18 or call_target(epilogue,EPILOGUE+4,EPILOGUE)!=REST or word(epilogue,0x14)!=BLR:
        raise ValueError("original EXIGetID epilogue/restorer changed")
    return exi,prefix,epilogue

def make(owner:Path)->bytes:
    prev=make_v54(owner)
    raw=owner.read_bytes()
    exi,prefix,epilogue=verify_original(raw)
    text,data=sections_of(prev)
    if len(text)!=7 or len(data)!=2:
        raise ValueError("V54 Wii DOL segment count differs")
    for addr,n in ((SAVE,0x28),(REST,0x28)):
        hit=[(base,code) for base,code in text if base<=addr and addr+n<=base+len(code)]
        if len(hit)!=1 or hit[0][1][addr-hit[0][0]:addr-hit[0][0]+n]!=text_at(raw,addr,n):
            raise ValueError("V54 inherited original register save/restore helpers differ")
    base,code=text[6]
    if (len(code)!=OLD_STOP+8-base or
        code[EXI-base:OLD_STOP-base]!=exi[:OLD_STOP-EXI] or
        code[OLD_STOP-base:]!=struct.pack(">II",SC,BLR)):
        raise ValueError("V54 original EXI prefix/test boundary differs")
    code[OLD_STOP-base:]=exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
    if len(code)!=STOP+8-base:
        raise ValueError("V55 EXI test stop length incorrect")
    gap=ID-(base+len(code))
    if gap<0 or gap%4 or gap>0x10000:
        raise ValueError("V55 cannot fit original EXIGetID after EXIInit")
    code.extend(struct.pack(">I",NOP)*(gap//4))
    code.extend(prefix)
    code.extend(struct.pack(">II",SC,BLR))
    tail_gap=EPILOGUE-(base+len(code))
    if tail_gap<0 or tail_gap%4 or tail_gap>0x10000:
        raise ValueError("V55 original EXIGetID epilogue placement invalid")
    code.extend(struct.pack(">I",NOP)*(tail_gap//4))
    code.extend(epilogue)
    if len(code)!=EPILOGUE_END-base:
        raise ValueError("V55 EXIGetID epilogue section length changed")
    text[6]=(base,code)
    out=bytearray(prev[:256])
    for i,(guest,blob) in enumerate(text):
        at=len(out)
        for h,v in ((0,at),(0x48,guest),(0x90,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    for i,(guest,blob) in enumerate(data):
        at=len(out)
        for h,v in ((0x1c,at),(0x64,guest),(0xac,len(blob))):
            struct.pack_into(">I",out,h+4*i,v)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    if word(out,0xE0)!=START:
        raise ValueError("original Wii __start entry changed")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("private_out",type=Path)
    a=p.parse_args()
    if a.private_out.exists() or a.private_out.is_symlink():
        p.error("refusing to overwrite original-derived private image")
    a.private_out.write_bytes(make(a.owner_dol))
    print("PASS: V55 private original Wii EXI cached ID fast-return fixture")
