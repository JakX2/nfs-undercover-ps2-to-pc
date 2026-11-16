#!/usr/bin/env python3
"""Restore authentic Wii interrupt-initializer return into original OSInit.

Only an SHA-256-pinned owner game DOL supplies original PPC words. The
private synthetic terminal at 0x805266AC is replaced with source-backed code.
The already-installed private OSInit stop is 0x805208BC.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_mask_bridge_v56 import make as v56, NEW_STOP as OLD_STOP, TIME_SECTION, NOP
from make_alarm_v47 import original_text, be32, call_target, SC, BLR

INT_END=0x805266E0
RESTORE=0x805265D4
SET_EXC=0x80520E9C
OSINIT_STOP=0x805208BC

def make(owner:Path)->bytes:
    data=bytearray(v56(owner))
    raw=owner.read_bytes()
    cont=original_text(raw,OLD_STOP,INT_END-OLD_STOP)
    restore=original_text(raw,RESTORE,0x24)
    if (len(cont)!=0x34 or len(restore)!=0x24 or
        call_target(cont,0x805266B0,OLD_STOP)!=RESTORE or
        call_target(cont,0x805266C0,OLD_STOP)!=SET_EXC or
        be32(cont,len(cont)-4)!=BLR or be32(restore,len(restore)-4)!=BLR):
        raise ValueError('V57 original interrupt return/handler callgraph changed')
    off=be32(data,4)
    base=be32(data,0x4c)
    size=be32(data,0x94)
    if base!=TIME_SECTION or off<0x100 or off+size>len(data):
        raise ValueError('V57 inherited interrupt segment geometry changed')
    pos=off+OLD_STOP-base
    if (pos<off or pos+len(cont)>off+size or be32(data,pos)!=SC or
        be32(data,pos+4)!=BLR or
        any(be32(data,pos+i)!=NOP for i in range(8,len(cont),4))):
        raise ValueError('V57 refused to overwrite original/private non-NOP text')
    restore_at=off+RESTORE-base
    if (restore_at<off or restore_at+len(restore)>off+size or
        data[restore_at:restore_at+len(restore)]!=restore):
        raise ValueError('V57 prerequisite authentic OSRestoreInterrupts body changed')
    firstoff=be32(data,0)
    firstbase=be32(data,0x48)
    if firstbase!=0x80520670 or be32(data,firstoff+OSINIT_STOP-firstbase)!=SC or \
       be32(data,firstoff+OSINIT_STOP-firstbase+4)!=BLR:
        raise ValueError('V57 missing inherited OSInit terminal')
    data[pos:pos+len(cont)]=cont
    return bytes(data)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_original_dol',type=Path)
    ap.add_argument('new_private_image',type=Path)
    a=ap.parse_args()
    if a.new_private_image.exists():ap.error('refusing existing private output')
    a.new_private_image.write_bytes(make(a.owner_original_dol))
    print('PASS: V57 source-backed Wii interrupt epilogue restored privately')
