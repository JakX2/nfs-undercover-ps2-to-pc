#!/usr/bin/env python3
"""Private V30 Wii OSInit hardware-init slice from owner SHA-pinned DOL.

Original PPC bytes are only read/written in the owner's local temporary image.
The OSReport path is an explicit TEST STOP, not a fake OSReport implementation.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_perf_v29 import (make as make_v29, be32, STOP as OLD_STOP,
                                  OSINIT, PERF0)
from make_osinit_execparams_v28 import (text_at, target, ALT, SC, BLR, NOP)

STOP = 0x80520700
OSREPORT = 0x80522F00
HID0_READ = 0x804B7920
HID0_WRITE = 0x804B7928
SPEC = 0x804B7A00
NONIEEE = 0x804B7A28
HID4 = 0x804B7A30
HID_END = HID4 + 80


def _spr(op):
    return (((op >> 11) & 31) << 5) | ((op >> 16) & 31)


def make(owner):
    old = make_v29(owner)  # verifies owner SHA and earlier OSInit originals
    raw = Path(owner).read_bytes()
    sections = []
    for i in range(7):
        off, addr, size = (be32(old, base+4*i) for base in (0,0x48,0x90))
        if not size or off < 256 or off+size > len(old):
            raise ValueError('invalid V29 base slice')
        sections.append((addr, bytearray(old[off:off+size])))
    assert sections[0][0] == OSINIT and sections[6][0] == PERF0

    # Genuine original instruction sequence at the three added BL call sites.
    continuation = text_at(raw,OLD_STOP,STOP-OLD_STOP)
    for callsite, destination in ((0x805206F4,HID4),
                                  (0x805206F8,SPEC),
                                  (0x805206FC,NONIEEE)):
        if target(be32(continuation,callsite-OLD_STOP),callsite,True)!=destination:
            raise ValueError('original OSInit hardware setup callsite differs')
    os = sections[0][1]
    if be32(os,OLD_STOP-OSINIT)!=SC or be32(os,ALT-OSINIT)!=SC:
        raise ValueError('V29 private test stops changed')
    os[OLD_STOP-OSINIT:STOP-OSINIT] = continuation
    struct.pack_into('>II',os,STOP-OSINIT,SC,BLR)
    # OSReport is a deliberate rejection boundary for the HID4-bit31-clear
    # branch. For this path, the ORIGINAL OSReport has NOT executed.
    os.extend(NOP.to_bytes(4,'big')*((OSREPORT+8-(OSINIT+len(os)))//4))
    if len(os)!=OSREPORT+8-OSINIT:
        raise ValueError('OSReport stop section alignment changed')
    struct.pack_into('>II',os,OSREPORT-OSINIT,SC,BLR)
    sections[0]=(OSINIT,os)

    low=text_at(raw,HID0_READ,16)
    perf=text_at(raw,PERF0,48)
    spec=text_at(raw,SPEC,40)
    non_ieee=text_at(raw,NONIEEE,8)
    hid4=text_at(raw,HID4,80)
    for body in (low[:8],low[8:],non_ieee,spec,hid4):
        if be32(body,len(body)-4)!=BLR:
            raise ValueError('source hardware helper missing complete return')
    if _spr(be32(low,0))!=1008 or _spr(be32(low,8))!=1008:
        raise ValueError('HID0 SPR mismatch')
    if _spr(be32(hid4,0x1c))!=1011 or _spr(be32(hid4,0x38))!=1011:
        raise ValueError('HID4 SPR mismatch')
    if target(be32(hid4,0x30),HID4+0x30,True)!=OSREPORT:
        raise ValueError('HID4 must branch to explicit OSReport stop')
    if target(be32(spec,0x0c),SPEC+0x0c,True)!=HID0_READ or \
       target(be32(spec,0x14),SPEC+0x14,True)!=HID0_WRITE:
        raise ValueError('original speculative HID0 control callgraph differs')
    if be32(non_ieee,0)!=0xFFA0004C:
        raise ValueError('expected genuine PowerPC mtfsb1 29')
    if bytes(sections[6][1])!=perf:
        raise ValueError('V29 performance helper bytes changed')
    hw=bytearray(NOP.to_bytes(4,'big')*((HID_END-HID0_READ)//4))
    for at, body in ((HID0_READ,low),(PERF0,perf),(SPEC,spec),
                     (NONIEEE,non_ieee),(HID4,hid4)):
        hw[at-HID0_READ:at-HID0_READ+len(body)]=body
    sections[6]=(HID0_READ,hw)
    out=bytearray(256+sum((len(s)+3)&~3 for _,s in sections))
    pos=256
    for i,(addr,payload) in enumerate(sections):
        for base,value in ((0,pos),(0x48,addr),(0x90,len(payload))):
            struct.pack_into('>I',out,base+4*i,value)
        out[pos:pos+len(payload)]=payload
        pos+=(len(payload)+3)&~3
    struct.pack_into('>I',out,0xE0,OSINIT)
    return bytes(out)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_dol',type=Path)
    ap.add_argument('output_private_dol',type=Path)
    args=ap.parse_args()
    if args.output_private_dol.exists():
        ap.error('private output already exists')
    image=make(args.original_dol)
    args.output_private_dol.write_bytes(image)
    print('PASS: V30 private original OSInit→HID4/speculation/FPSCR slice',len(image))
