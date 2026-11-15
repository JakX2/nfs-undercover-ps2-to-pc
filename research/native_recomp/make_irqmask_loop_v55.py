#!/usr/bin/env python3
"""Owner-private Wii interrupt initializer through the genuine SetInterruptMask loop.

No original game instructions appear in the distributed Python source.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_setmask_v54 import SHA, ENTRY as SETMASK, STOP as SETMASK_END, BLR, SC
from make_interrupt_prefix_v50 import extract, u32, target

IRQ=0x8052661C
STOP=0x805266AC
DISABLE=0x805265AC
MEMSET=0x8000443C
FILL=0x80004388


def make(owner:Path):
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError('owner original DOL SHA mismatch')
    irq=extract(raw,IRQ,STOP-IRQ)
    irq+=struct.pack('>II',SC,BLR)
    disable=extract(raw,DISABLE,0x14)
    setmask=extract(raw,SETMASK,SETMASK_END-SETMASK)
    fill=extract(raw,FILL,0xe4)
    if (target(u32(irq,0x2c),IRQ+0x2c)!=MEMSET or
        target(u32(irq,0x58),IRQ+0x58)!=DISABLE or
        target(u32(irq,0x84),IRQ+0x84)!=SETMASK or
        u32(disable,0x10)!=BLR or u32(setmask,len(setmask)-4)!=BLR or
        u32(fill,0xb0)!=BLR or u32(fill,0xe0)!=BLR):
        raise ValueError('original interrupt mask callgraph/helper return changed')
    sections=[(DISABLE,disable),(IRQ,irq),(SETMASK,setmask),(FILL,fill)]
    total=0x100+sum(len(data) for _,data in sections)
    out=bytearray(total)
    cursor=0x100
    for i,(addr,blob) in enumerate(sections):
        for header,value in ((0,cursor),(0x48,addr),(0x90,len(blob))):
            struct.pack_into('>I',out,header+4*i,value)
        out[cursor:cursor+len(blob)]=blob
        cursor+=len(blob)
    struct.pack_into('>I',out,0xe0,IRQ)
    return bytes(out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('original_owner_dol',type=Path)
    p.add_argument('private_output',type=Path)
    args=p.parse_args()
    if args.private_output.exists():p.error('refusing to overwrite private test image')
    args.private_output.write_bytes(make(args.original_owner_dol))
    print('PASS: V55 private original Wii interrupt-mask loop fixture created')
