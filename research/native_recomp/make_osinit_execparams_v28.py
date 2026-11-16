#!/usr/bin/env python3
"""Privately build a bounded original Wii OSInit→exec-params AOT test image.

No proprietary PowerPC instruction bytes are embedded in distributed source.
Input is SHA-256-pinned owner DOL; outputs are private scratch data only.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
OSINIT = 0x80520670
STOP = 0x805206C0
ALT = 0x80520BDC
TIME = 0x8052A844
GETTIME = 0x8052A824
DISABLE = 0x805265AC
RESTORE = 0x805265D4
EXEC = 0x80523B1C
SAVE = 0x805450E8
COPY = 0x80004338
SC, BLR, NOP = 0x44000002, 0x4E800020, 0x60000000


def be32(blob, off):
    return struct.unpack_from('>I', blob, off)[0]


def text_at(blob, addr, size):
    if size <= 0 or size & 3 or addr & 3:
        raise ValueError('unaligned Wii text request')
    for i in range(7):
        offset, guest, length = (be32(blob, section + i * 4)
                                 for section in (0, 0x48, 0x90))
        if length and guest <= addr and addr + size <= guest + length:
            where = offset + addr - guest
            if offset < 256 or where + size > len(blob):
                raise ValueError('truncated DOL code')
            return blob[where:where + size]
    raise ValueError(f'missing code at {addr:08X}')


def target(word, at, link):
    if word >> 26 != 18 or bool(word & 1) != link:
        raise ValueError(f'wrong branch at {at:08X}')
    disp = word & 0x03FFFFFC
    if disp & 0x02000000:
        disp -= 0x04000000
    return (disp if word & 2 else at + disp) & 0xFFFFFFFF


def make(path):
    source = Path(path).read_bytes()
    if hashlib.sha256(source).hexdigest() != ORIGINAL_SHA:
        raise ValueError('owner DOL SHA-256 mismatch')
    prefix = text_at(source, OSINIT, STOP-OSINIT)
    expected = {OSINIT+0x10: SAVE, OSINIT+0x38: TIME,
                OSINIT+0x44: DISABLE, OSINIT+0x4C: EXEC}
    for pc, dest in expected.items():
        if target(be32(prefix, pc-OSINIT), pc, True) != dest:
            raise ValueError('original OSInit callgraph changed')
    if (be32(prefix, 0) != 0x9421FFB0 or
            be32(prefix, 0x34) != 0x900DF21C or
            be32(prefix, 0x3C) != 0x908DF254 or
            be32(prefix, 0x40) != 0x906DF250):
        raise ValueError('original OSInit prologue/time stores changed')
    os = bytearray(NOP.to_bytes(4, 'big') * ((ALT+8-OSINIT)//4))
    os[:len(prefix)] = prefix
    struct.pack_into('>II', os, STOP-OSINIT, SC, BLR)
    struct.pack_into('>II', os, ALT-OSINIT, SC, BLR)
    time = text_at(source, GETTIME, TIME+100-GETTIME)
    irq = bytearray(text_at(source, DISABLE, RESTORE+36-DISABLE))
    # The gap includes unused OSEnableInterrupts. It is deliberately NOP-only.
    irq[20:RESTORE-DISABLE] = NOP.to_bytes(4,'big')*((RESTORE-DISABLE-20)//4)
    execparams = text_at(source, EXEC, 36)
    saver = text_at(source, SAVE, 52)
    copier = text_at(source, COPY, 80)
    if any(be32(body,len(body)-4)!=BLR for body in (time[-100:], time[:24],
            irq[:20], irq[RESTORE-DISABLE:], execparams, saver, copier)):
        raise ValueError('original helper return changed')
    if target(be32(execparams,20),EXEC+20,False)!=COPY or be32(execparams,16)!=0x38A0001C:
        raise ValueError('original exec-params transfer changed')
    texts = [(OSINIT, bytes(os)), (GETTIME, time), (DISABLE, bytes(irq)),
             (EXEC,execparams), (SAVE,saver), (COPY,copier)]
    output = bytearray(256+sum((len(body)+3)&~3 for _,body in texts))
    ptr = 256
    for index,(guest,payload) in enumerate(texts):
        for base,value in ((0,ptr),(0x48,guest),(0x90,len(payload))):
            struct.pack_into('>I',output,base+4*index,value)
        output[ptr:ptr+len(payload)] = payload
        ptr += (len(payload)+3)&~3
    struct.pack_into('>I',output,0xE0,OSINIT)
    return bytes(output)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_dol',type=Path)
    ap.add_argument('output_private_dol',type=Path)
    args=ap.parse_args()
    if args.output_private_dol.exists():
        ap.error('refusing overwrite of existing private image')
    result=make(args.original_dol)
    args.output_private_dol.write_bytes(result)
    print('PASS: V28 original Wii OSInit→exec-params bounded private image; bytes=',len(result))
