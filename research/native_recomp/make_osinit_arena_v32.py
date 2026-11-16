#!/usr/bin/env python3
"""Private, SHA-pinned Undercover Wii OSInit MEM1 arena setter fixture.

No game PowerPC instruction bytes are distributed. Source slices exist only in
user-local scratch after validating the unchanged owner DOL through V31.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_lowmem_v31 import make as make_v31, STOP as OLD_STOP
from make_osinit_hid4_v30 import OSINIT, be32
from make_osinit_execparams_v28 import text_at, target, SC, BLR

STOP = 0x80520818
LO = 0x80521D60
HI = 0x80521D48


def conditional_target(op, address):
    if op >> 26 != 16 or (op & 3):
        raise ValueError('unexpected arena conditional branch')
    diff = op & 0xfffc
    if diff & 0x8000:
        diff -= 0x10000
    return (address + diff) & 0xffffffff


def validate_os(text):
    if len(text) != STOP - OLD_STOP:
        raise ValueError('arena continuation truncated')
    for site, destination in ((0x8052077c, 0x805207e8),
                              (0x8052078c, 0x805207e4),
                              (0x8052079c, 0x805207a4),
                              (0x805207b4, 0x805207e8),
                              (0x805207c0, 0x805207e8),
                              (0x805207cc, 0x805207e8),
                              (0x805207f8, 0x80520814),
                              (0x80520808, 0x80520814)):
        if conditional_target(be32(text,site-OLD_STOP), site) != destination:
            raise ValueError(f'changed original MEM1 conditional edge at {site:08X}')
    for site, destination in ((0x805207a0, 0x805207a8),
                              (0x805207e0, 0x805207e8)):
        if target(be32(text,site-OLD_STOP),site,False) != destination:
            raise ValueError(f'changed original MEM1 direct edge at {site:08X}')
    for site, destination in ((0x805207e8, LO), (0x80520814, HI)):
        if target(be32(text,site-OLD_STOP),site,True) != destination:
            raise ValueError(f'changed original MEM1 setter call at {site:08X}')
    for site in (0x80520778,0x80520798,0x805207b0,0x805207bc,
                 0x805207c8,0x805207f4,0x80520804):
        if be32(text,site-OLD_STOP)>>26 not in (10,11):
            raise ValueError(f'expected original MEM1 comparison at {site:08X}')
    for site, class_ in ((0x80520794,32), (0x805207ac,32),
                         (0x805207b8,32), (0x805207c4,32),
                         (0x805207f0,32), (0x80520800,32)):
        if be32(text,site-OLD_STOP)>>26 != class_:
            raise ValueError(f'original MEM1 memory read changed at {site:08X}')
    # Fail closed if the original candidate zero-mask or fallback constants change.
    for site, kind in ((0x80520788,21),(0x805207dc,21)):
        if be32(text,site-OLD_STOP)>>26 != kind:
            raise ValueError('MEM1 alignment or mask changed')
    if be32(text,0x8052080c-OLD_STOP)>>26 != 15:
        raise ValueError('MEM1 high fallback address changed')


def validate_setter(blob, guest):
    if len(blob)!=8 or be32(blob,4)!=BLR:
        raise ValueError('short/invalid original Wii MEM1 setter')
    op=be32(blob,0)
    if op>>26!=36 or ((op>>21)&31)!=3 or ((op>>16)&31)!=13:
        raise ValueError('MEM1 setter GPR/base opcode changed')
    disp=op&0xffff
    if disp&0x8000:disp-=0x10000
    if disp != (-16400 if guest==LO else -3472):
        raise ValueError('MEM1 arena global location changed')


def make(owner):
    prior=make_v31(owner)
    src=Path(owner).read_bytes()
    continuation=text_at(src,OLD_STOP,STOP-OLD_STOP)
    validate_os(continuation)
    original_setters={guest:text_at(src,guest,8) for guest in (HI,LO)}
    for guest,body in original_setters.items():validate_setter(body,guest)
    sections=[]
    for i in range(7):
        off,addr,length=(be32(prior,base+i*4) for base in (0,0x48,0x90))
        if off<256 or not length or off+length>len(prior):
            raise ValueError('V31 parent test DOL section geometry changed')
        sections.append((addr,bytearray(prior[off:off+length])))
    os_addr,os=sections[0]
    if os_addr!=OSINIT or be32(os,OLD_STOP-OSINIT)!=SC:
        raise ValueError('V31 synthetic terminal boundary changed')
    if os_addr+len(os)<LO+8:
        raise ValueError('parent fixture lacks arena helper region')
    os[OLD_STOP-OSINIT:STOP-OSINIT]=continuation
    struct.pack_into('>II',os,STOP-OSINIT,SC,BLR)
    for guest,body in original_setters.items():
        # V31 padded unused addresses with synthetic NOPs.
        start=guest-OSINIT
        if any(be32(os,start+i)!=0x60000000 for i in (0,4)):
            raise ValueError('arena setter fixture padding unexpectedly occupied')
        os[start:start+8]=body
    sections[0]=(os_addr,os)
    result=bytearray(256+sum((len(body)+3)&~3 for _,body in sections))
    pos=256
    for i,(guest,body) in enumerate(sections):
        for base,value in ((0,pos),(0x48,guest),(0x90,len(body))):
            struct.pack_into('>I',result,base+4*i,value)
        result[pos:pos+len(body)]=body
        pos+=(len(body)+3)&~3
    struct.pack_into('>I',result,0xE0,OSINIT)
    return bytes(result)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_dol',type=Path)
    p.add_argument('destination',type=Path)
    a=p.parse_args()
    if a.destination.exists():p.error('refusing to overwrite private DOL')
    data=make(a.owner_dol)
    a.destination.write_bytes(data)
    print('PASS: V32 owner-SHA-pinned private MEM1 arena image, bytes=',len(data))
