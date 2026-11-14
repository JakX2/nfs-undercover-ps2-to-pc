#!/usr/bin/env python3
"""Original-free, SHA-pinned private Wii OSInit MEM2 arena continuation.

Extracts verified owner-only code into a bounded synthetic DOL. No original
instructions or generated game C++ are included in the published sources.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_arena_v32 import make as make_v32, STOP as OLD_STOP, OSINIT, be32
from make_osinit_execparams_v28 import text_at, target, SC, BLR

STOP = 0x805208A4
MEM2_LO = 0x80521D68
MEM2_HI = 0x80521D50


def check_source(code):
    if len(code) != STOP - OLD_STOP:
        raise ValueError('original MEM2 continuation truncated')
    for site, destination in ((0x80520824, 0x80520890),
                              (0x8052083c, 0x80520870),
                              (0x8052084c, 0x8052088c),
                              (0x80520858, 0x8052088c),
                              (0x80520878, 0x8052088c),
                              (0x80520884, 0x8052088c),
                              (0x8052089c, 0x805208a4)):
        op=be32(code, site-OLD_STOP)
        if op >> 26 != 16 or (op & 3):
            raise ValueError(f'unexpected MEM2 conditional branch at {site:08x}')
        d=op & 0xfffc
        if d & 0x8000: d -= 0x10000
        if (site+d)&0xffffffff != destination:
            raise ValueError(f'changed MEM2 branch target at {site:08x}')
    for site, destination in ((0x8052088c,MEM2_LO),(0x805208a0,MEM2_HI)):
        if target(be32(code,site-OLD_STOP),site,True)!=destination:
            raise ValueError(f'changed original MEM2 setter call at {site:08x}')
    for pc, op_class in ((0x8052081c,32),(0x80520840,32),
                         (0x80520850,32),(0x80520894,32)):
        if be32(code,pc-OLD_STOP)>>26 != op_class:
            raise ValueError(f'changed MEM2 guest memory read at {pc:08x}')
    if (be32(code,0x80520818-OLD_STOP) != 0x3c608000 or
        be32(code,0x80520890-OLD_STOP) != 0x3c608000):
        raise ValueError('low-memory MEM2 arena hint base changed')


def check_setter(blob, guest):
    if len(blob)!=8 or be32(blob,4)!=BLR:
        raise ValueError('short original MEM2 setter body')
    op=be32(blob,0)
    displacement = struct.unpack('>h',blob[2:4])[0]
    if op>>26!=36 or ((op>>21)&31)!=3 or ((op>>16)&31)!=13 or displacement != (-16396 if guest==MEM2_LO else -3468):
        raise ValueError('original MEM2 setter store operand changed')


def make(owner):
    previous=make_v32(owner)   # SHA and V32 source checks remain mandatory
    raw=Path(owner).read_bytes()
    continuation=text_at(raw,OLD_STOP,STOP-OLD_STOP)
    check_source(continuation)
    helpers={guest:text_at(raw,guest,8) for guest in (MEM2_HI,MEM2_LO)}
    for guest,body in helpers.items():check_setter(body,guest)
    sections=[]
    for i in range(7):
        off,addr,length=(be32(previous,x+i*4) for x in (0,0x48,0x90))
        if off<256 or not length or off+length>len(previous):
            raise ValueError('V32 private DOL section geometry corrupted')
        sections.append((addr,bytearray(previous[off:off+length])))
    addr,code=sections[0]
    if addr!=OSINIT or be32(code,OLD_STOP-OSINIT)!=SC:
        raise ValueError('V32 termination boundary changed')
    if addr+len(code)<max(helpers)+8:
        raise ValueError('parent image does not contain MEM2 helper slots')
    code[OLD_STOP-OSINIT:STOP-OSINIT]=continuation
    struct.pack_into('>II',code,STOP-OSINIT,SC,BLR)
    for guest,body in helpers.items():
        at=guest-OSINIT
        if any(be32(code,at+i)!=0x60000000 for i in (0,4)):
            raise ValueError('previously unoccupied MEM2 setter slot overwritten')
        code[at:at+8]=body
    sections[0]=(addr,code)
    image=bytearray(256+sum((len(chunk)+3)&~3 for _,chunk in sections))
    pos=256
    for i,(guest,chunk) in enumerate(sections):
        for base,value in ((0,pos),(0x48,guest),(0x90,len(chunk))):
            struct.pack_into('>I',image,base+i*4,value)
        image[pos:pos+len(chunk)]=chunk
        pos+=(len(chunk)+3)&~3
    struct.pack_into('>I',image,0xe0,OSINIT)
    return bytes(image)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_dol',type=Path)
    p.add_argument('destination',type=Path)
    args=p.parse_args()
    if args.destination.exists():p.error('refusing to overwrite private test DOL')
    image=make(args.owner_dol)
    args.destination.write_bytes(image)
    print('PASS: owner-SHA-verified bounded OSInit MEM2 test DOL size:',len(image))
