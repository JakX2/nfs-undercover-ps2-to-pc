#!/usr/bin/env python3
"""Owner-local V29 original OSInit performance-register startup test slice.

Uses the original SHA-checked Wii DOL and the independently authored V28
fixture builder. Original PowerPC code is extracted privately at runtime;
never package the resulting DOL or NWiiRecomp-generated game C++.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_execparams_v28 import (make as make_v28, be32, text_at,
                                       OSINIT, ALT, SC, BLR)

PREVIOUS_STOP = 0x805206C0
STOP = 0x805206F0
PERF0 = 0x804B7964
PERF_TARGETS = (952, 956, 953, 954, 957, 958)  # MMCR0, MMCR1, PMC1-4


def spr_opcode(w):
    if w >> 26 != 31 or (w >> 1) & 0x3ff != 467 or (w >> 21) & 31 != 3:
        raise ValueError('original performance helper is not mtspr r3')
    return (((w >> 11) & 31) << 5) | ((w >> 16) & 31)


def make(original_dol):
    prev = make_v28(original_dol)  # verifies owner SHA and preceding PPC calls
    original = Path(original_dol).read_bytes()
    sections = []
    for i in range(6):
        off, address, size = (be32(prev,base+i*4) for base in (0,0x48,0x90))
        if off < 256 or not size or off + size > len(prev):
            raise ValueError('malformed V28 parent DOL')
        sections.append((address,bytearray(prev[off:off+size])))
    if sections[0][0] != OSINIT:
        raise ValueError('wrong bounded OSInit address')
    # Preserve the authentic new PPC instructions, including all six callsites.
    new_os = text_at(original, PREVIOUS_STOP, STOP-PREVIOUS_STOP)
    os = sections[0][1]
    if be32(os,PREVIOUS_STOP-OSINIT) != SC:
        raise ValueError('previous boundary is not an explicit synthetic stop')
    os[PREVIOUS_STOP-OSINIT:STOP-OSINIT] = new_os
    struct.pack_into('>II',os,STOP-OSINIT,SC,BLR)
    sections[0] = (OSINIT,os)
    perf = text_at(original,PERF0,6*8)
    for i,spr in enumerate(PERF_TARGETS):
        if spr_opcode(be32(perf,i*8)) != spr or be32(perf,i*8+4) != BLR:
            raise ValueError('original Wii performance helper shape changed')
    sections.append((PERF0,bytearray(perf)))
    result = bytearray(256+sum((len(raw)+3)&~3 for _,raw in sections))
    pos = 256
    for i,(addr,body) in enumerate(sections):
        for base,value in ((0,pos),(0x48,addr),(0x90,len(body))):
            struct.pack_into('>I',result,base+4*i,value)
        result[pos:pos+len(body)] = body
        pos += (len(body)+3)&~3
    struct.pack_into('>I',result,0xE0,OSINIT)
    return bytes(result)


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_dol',type=Path)
    ap.add_argument('output_private_dol',type=Path)
    args=ap.parse_args()
    if args.output_private_dol.exists():
        ap.error('refusing overwrite of existing private DOL')
    result=make(args.original_dol)
    args.output_private_dol.write_bytes(result)
    print('PASS: V29 private original OSInit→MMCR/PMC bounded image, bytes=',len(result))
