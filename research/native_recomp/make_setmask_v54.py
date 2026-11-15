#!/usr/bin/env python3
"""Build private, SHA-pinned original Wii SetInterruptMask function test DOL.

Only the user-provided DOL supplies original PPC instructions; never commit the private output.
"""
import argparse
import hashlib
import struct
from pathlib import Path

SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY=0x805266E0
STOP=0x8052693C
SC=0x44000002
BLR=0x4E800020

def be32(data,off):return struct.unpack_from('>I',data,off)[0]

def extract(data,addr,length):
    for i in range(7):
        off=be32(data,i*4)
        start=be32(data,0x48+i*4)
        size=be32(data,0x90+i*4)
        if size and start<=addr and addr+length<=start+size:
            pos=off+addr-start
            if off<0x100 or pos+length>len(data):raise ValueError('original Wii DOL text bounds invalid')
            return data[pos:pos+length]
    raise ValueError('original PPC function absent from owner text sections')

def make(owner):
    data=owner.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('original owner Wii DOL SHA-256 mismatch')
    original=extract(data,ENTRY,STOP-ENTRY)
    # Structural instruction checks without embedding any proprietary function bytes.
    if be32(original,0)>>26!=31 or be32(original,0x258)!=BLR:
        raise ValueError('unexpected original SetInterruptMask entry or return')
    # Verified original exit sites; pin these to avoid silently accepting mis-sliced text.
    for address in (0x80526708,0x80526778,0x805267b8,0x805267e4,
                    0x80526828,0x8052686c,0x805268a0,0x80526938):
        if be32(original,address-ENTRY)!=BLR:
            raise ValueError('required original PowerPC function return changed')
    body=original+struct.pack('>II',SC,BLR)
    out=bytearray(0x100+len(body))
    for off,value in ((0,0x100),(0x48,ENTRY),(0x90,len(body)),(0xE0,ENTRY)):
        struct.pack_into('>I',out,off,value)
    out[0x100:]=body
    return bytes(out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_dol',type=Path)
    p.add_argument('private_output',type=Path)
    a=p.parse_args()
    if a.private_output.exists():p.error('refusing to overwrite private output')
    a.private_output.write_bytes(make(a.owner_original_dol))
    print('PASS: V54 SHA-pinned original SetInterruptMask slice created privately')
