#!/usr/bin/env python3
"""Build a private original Wii OSSetErrorHandler AOT test; no copyrighted bytes embedded.

Original code is sliced only from the SHA-pinned owner's DOL. The synthetic SC/BLR
at the exact return address is used only to end tests. No original code is published.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ERROR = 0x805230B8
ERROR_END = 0x80523340
DISABLE = 0x805265AC
RESTORE = 0x805265D4
HELPER_END = 0x805265F8
MSR = 0x804B7910
FP_END = 0x804B79DC
SC = 0x44000002
BLR = 0x4E800020
NOP = 0x60000000

def read_u32(buf,off): return struct.unpack_from('>I',buf,off)[0]
def extract(source,pc,size):
    for index in range(7):
        off=read_u32(source,4*index)
        base=read_u32(source,0x48+4*index)
        length=read_u32(source,0x90+4*index)
        if off>=0x100 and base<=pc and pc+size<=base+length and off+length<=len(source):
            return bytes(source[off+pc-base:off+pc-base+size])
    raise ValueError(f'owner-original PPC not mapped at {pc:#x}')
def target(op,pc):
    if op>>26!=18 or not(op&1):raise ValueError(f'missing original bl at {pc:#x}')
    disp=op&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    return disp if(op&2) else (pc+disp)&0xffffffff

def make(owner):
    data=owner.read_bytes()
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('V63 rejected unexpected original Wii DOL SHA-256')
    func=extract(data,ERROR,ERROR_END-ERROR)
    helpers=extract(data,DISABLE,HELPER_END-DISABLE)
    fp=extract(data,MSR,FP_END-MSR)
    # Preserve the full original function and all target-branch code. The only
    # synthetic opcodes are separate NOP gap and our explicit terminal stop.
    if (len(func)!=0x288 or read_u32(func,len(func)-4)!=BLR or
        read_u32(helpers,DISABLE+0x10-DISABLE)!=BLR or
        read_u32(helpers,RESTORE-DISABLE+0x20)!=BLR or
        read_u32(fp,4)!=BLR or read_u32(fp,12)!=BLR):
        raise ValueError('V63 original Wii function extents or returns changed')
    calls={0x805230DC:DISABLE,0x80523100:MSR,0x8052310C:MSR+8,
           0x80523110:0x804B7994,0x80523308:0x804B79B4,
           0x80523310:MSR+8,0x80523318:RESTORE}
    for pc,dest in calls.items():
        if target(read_u32(func,pc-ERROR),pc)!=dest:
            raise ValueError(f'V63 owner-original call changed at {pc:#x}')
    # Three bounded text sections. Index 16's FPU branch remains translated
    # but is NOT executed in this milestone.
    ranges=((ERROR,func+struct.pack('>II',SC,BLR)),(DISABLE,helpers),(MSR,fp))
    size=0x100+sum(len(b) for _,b in ranges)
    output=bytearray(size)
    offset=0x100
    for i,(base,body) in enumerate(ranges):
        for field,val in ((4*i,offset),(0x48+4*i,base),(0x90+4*i,len(body))):
            struct.pack_into('>I',output,field,val)
        output[offset:offset+len(body)]=body
        offset+=len(body)
    struct.pack_into('>I',output,0xE0,ERROR)
    return bytes(output)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_wii_dol',type=Path)
    p.add_argument('private_output_dol',type=Path)
    a=p.parse_args()
    if a.private_output_dol.exists():p.error('refusing to overwrite private output')
    a.private_output_dol.write_bytes(make(a.owner_original_wii_dol))
    print('PASS: V63 owner-original OSSetErrorHandler private source fixture built')
