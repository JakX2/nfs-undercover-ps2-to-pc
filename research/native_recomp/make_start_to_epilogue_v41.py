#!/usr/bin/env python3
"""Private V41 continuous __start -> original OSExceptionInit return.

The owner-original DOL alone supplies PPC instructions. The debug callback
remains a conspicuous synthetic syscall stub; the real _restgpr_20 and
OSExceptionInit epilogue execute as native AOT translations. This is NOT a
real DBPrintf implementation and does not indicate a complete OS boot.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct

from make_start_to_vectors_v40 import make as make_v40, STOP as OLD_STOP
from make_start_to_vectorcopy_v38 import OSINIT, word
from make_osinit_execparams_v28 import text_at, target, SC, BLR, NOP
from make_osinit_syscall_bridge_v46 import (
    EXCEPTION_RETURN_START, EXCEPTION_RETURN_END, DEBUG_PRINT,
    RESTORE, RESTORE_END, SAVE, OLD_OSINIT_STOP
)

STOP=OLD_OSINIT_STOP
START=0x8000403C

def sections_of(raw:bytes):
    text=[]
    for i in range(7):
        off,guest,length=(word(raw,k+4*i) for k in (0,0x48,0x90))
        if off<256 or length<4 or off+length>len(raw):
            raise ValueError("V41 inherited continuous DOL text section invalid")
        text.append((guest,bytearray(raw[off:off+length])))
    data=[]
    for i in range(2):
        off,guest,length=(word(raw,k+4*i) for k in (0x1c,0x64,0xac))
        if off<256 or length<=0 or off+length>len(raw):
            raise ValueError("V41 inherited startup table/template missing")
        data.append((guest,bytes(raw[off:off+length])))
    if len({addr for addr,_ in text})!=7 or [x[0] for x in data]!=[0x80006420,0x90050000]:
        raise ValueError("V41 inherited DOL sections or oracle locations changed")
    if [len(x[1]) for x in data]!=[0xB0,0x98]:
        raise ValueError("V41 inherited startup/oracle payload sizes changed")
    return text,data

def make(owner:Path)->bytes:
    prior=make_v40(owner) # verifies exact owner SHA and every earlier original
    original=owner.read_bytes()
    if OLD_STOP!=0x80520E58 or STOP!=0x805208AC:
        raise ValueError("V41 original exception/OSInit PC bounds changed")
    tail=text_at(original,EXCEPTION_RETURN_START,
                 EXCEPTION_RETURN_END-EXCEPTION_RETURN_START)
    restore=text_at(original,RESTORE,RESTORE_END-RESTORE)
    if len(tail)!=0x1C or len(restore)!=0x34:
        raise ValueError("V41 owner original exception return helpers truncated")
    if (target(word(tail,0),EXCEPTION_RETURN_START,True)!=DEBUG_PRINT or
        target(word(tail,8),EXCEPTION_RETURN_START+8,True)!=RESTORE or
        word(tail,len(tail)-4)!=BLR or word(restore,len(restore)-4)!=BLR):
        raise ValueError("V41 original DBPrintf/restore/exception return changed")

    text,data=sections_of(prior)
    os_indices=[i for i,(addr,body) in enumerate(text)
                if addr<=OSINIT and EXCEPTION_RETURN_END<=addr+len(body)]
    if len(os_indices)!=1:
        raise ValueError("V41 OSInit/exception body not mapped uniquely")
    os_idx=os_indices[0]
    os_guest,os=text[os_idx]
    if os_guest!=OSINIT:
        raise ValueError("V41 inherited OSInit section address differs")
    at=EXCEPTION_RETURN_START-os_guest
    if os[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V40 test-only exception terminal was modified")
    if os[at+8:at+len(tail)]!=struct.pack(">I",NOP)*((len(tail)-8)//4):
        raise ValueError("V41 exception epilogue would overwrite translated guest code")
    stop_at=STOP-os_guest
    if os[stop_at:stop_at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V41 OSInit return checkpoint changed")
    os[at:at+len(tail)]=tail
    text[os_idx]=(os_guest,os)

    owners=[i for i,(guest,body) in enumerate(text) if guest<=SAVE<guest+len(body)]
    if len(owners)!=1:
        raise ValueError("V41 original register-save thunk not mapped uniquely")
    save_idx=owners[0]
    base,save=text[save_idx]
    offset=SAVE-base
    if save[offset:offset+0x34]!=text_at(original,SAVE,0x34):
        raise ValueError("V41 existing original save helper differs from owner DOL")
    extension=RESTORE_END-(base+len(save))
    if extension>0:
        if extension>0x100 or extension%4:
            raise ValueError("V41 original restore helper extension exceeds safe limit")
        save.extend(struct.pack(">I",NOP)*(extension//4))
    restore_at=RESTORE-base
    if restore_at<0 or restore_at+len(restore)>len(save):
        raise ValueError("V41 restore thunk cannot be placed in save section")
    if save[restore_at:restore_at+len(restore)]!=struct.pack(">I",NOP)*(len(restore)//4):
        raise ValueError("V41 original register-restore thunk overlaps existing code")
    for i,(guest,code) in enumerate(text):
        if i!=save_idx and guest<RESTORE_END and guest+len(code)>RESTORE:
            raise ValueError("V41 restore helper overlaps an independent DOL section")
    save[restore_at:restore_at+len(restore)]=restore
    text[save_idx]=(base,save)
    # The inherited original DBPrintf service is still a test-only sc;blr
    # stub. Never silently replace it with a returning host implementation.
    debug=[(guest,body) for guest,body in text
           if guest<=DEBUG_PRINT and DEBUG_PRINT+8<=guest+len(body)]
    if len(debug)!=1 or debug[0][1][DEBUG_PRINT-debug[0][0]:
                                  DEBUG_PRINT-debug[0][0]+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V41 synthetic DBPrintf boundary missing or overwritten")

    out=bytearray(prior[:256])
    for i,(guest,body) in enumerate(text):
        off=len(out)
        for field,value in ((0,off),(0x48,guest),(0x90,len(body))):
            struct.pack_into(">I",out,field+4*i,value)
        out.extend(body)
        out.extend(b"\0"*((-len(out))%4))
    for i,(guest,body) in enumerate(data):
        off=len(out)
        for field,value in ((0x1c,off),(0x64,guest),(0xac,len(body))):
            struct.pack_into(">I",out,field+4*i,value)
        out.extend(body)
        out.extend(b"\0"*((-len(out))%4))
    if word(out,0xe0)!=START:
        raise ValueError("V41 original Wii entry changed")
    return bytes(out)

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("owner_original_dol",type=Path)
    ap.add_argument("private_fixture",type=Path)
    a=ap.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        ap.error("refusing overwrite of private V41 DOL")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: original Wii continuous V41 exception-return fixture built privately")
