#!/usr/bin/env python3
"""Owner-private authentic Wii interrupt-handler table initialization test fixture.

The original PowerPC instruction bodies are read solely from the SHA-pinned
owner's DOL; the source-only toolkit contains no extracted game code.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY = 0x8052661C
CALL = 0x80526648
STOP = 0x8052664C
MEMSET = 0x8000443C
FILL = 0x80004388
BLR, SC = 0x4E800020, 0x44000002


def u32(data, at):
    return struct.unpack_from('>I', data, at)[0]


def extract(raw, address, length):
    if address % 4 or length <= 0 or length % 4:
        raise ValueError('invalid original text address or length')
    for i in range(7):
        off, start, size=(u32(raw,base+4*i) for base in (0,0x48,0x90))
        if size and start<=address and address+length<=start+size:
            pos=off+address-start
            if off<0x100 or pos+length>len(raw):
                raise ValueError('truncated original code section')
            return bytes(raw[pos:pos+length])
    raise ValueError('original PowerPC code not found in text section')


def target(op, pc):
    if op>>26 != 18 or op&1 != 1:
        raise ValueError('original interrupt initializer does not BL to memset')
    delta=op&0x03fffffc
    if delta&0x02000000:delta-=0x04000000
    return (delta if op&2 else pc+delta)&0xffffffff


def make(path):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('owner Wii DOL SHA-256 mismatch')
    prefix=extract(raw,ENTRY,STOP-ENTRY)
    helper=extract(raw,FILL,0xE4)
    if target(u32(prefix,CALL-ENTRY),CALL)!=MEMSET:
        raise ValueError('original __OSInterruptInit memcpy callgraph changed')
    if u32(helper,0xB0)!=BLR or u32(helper,0xE0)!=BLR:
        raise ValueError('original memset/fill helper return changed')
    # Two text sections, no initialized data. The test-only stop follows the
    # original call to memset; the original hardware/MMIO writes do NOT run.
    sections=[(ENTRY,prefix+struct.pack('>II',SC,BLR)),(FILL,helper)]
    payload=bytearray(0x100+sum(len(b) for _,b in sections))
    pos=0x100
    for i,(addr,body) in enumerate(sections):
        for offset,value in ((0,pos),(0x48,addr),(0x90,len(body))):
            struct.pack_into('>I',payload,offset+4*i,value)
        payload[pos:pos+len(body)]=body
        pos+=len(body)
    struct.pack_into('>I',payload,0xe0,ENTRY)
    return bytes(payload)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_owner_dol',type=Path)
    ap.add_argument('private_output',type=Path)
    args=ap.parse_args()
    if args.private_output.exists():ap.error('refusing to overwrite private test DOL')
    args.private_output.write_bytes(make(args.original_owner_dol))
    print('PASS: V50 owner-private interrupt/memset native test image created')
