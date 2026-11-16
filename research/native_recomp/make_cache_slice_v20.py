#!/usr/bin/env python3
"""Owner-private original __OSCacheInit plus original L2CR/MSR helpers.

Never distribute generated owner-derived DOLs. All other missing Wii services
are explicit original-free `sc; blr` test-only boundaries.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from make_fprinit_slice_v19 import make as make_v19
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, STOP, bl, linked_target
from make_psinit_slice_v18 import PS, HID_READ, HID_WRITE, IC, FPR, CACHE

CACHE_BYTES = 312
L2_READ = 0x804B7930
L2_WRITE = 0x804B7938
HID0_READ = 0x804B7920
MSR_READ = 0x804B7910
MSR_WRITE = 0x804B7918
DC_ENABLE = 0x80522280
IC_ENABLE = 0x805223BC
DEBUG_PRINT = 0x804E50B8
ERROR_HANDLER = 0x805230B8


def word(code):
    return struct.pack('>I', code)


def pad(addr, length):
    if (addr & 3) or (length & 3):
        raise ValueError('unaligned synthetic helper span')
    return bytearray(word(0x60000000) * (length // 4))


def spr(reg, number, xo):
    return (31 << 26) | (reg << 21) | ((number & 31) << 16) | (((number >> 5) & 31) << 11) | (xo << 1)


def synthetic_helper_region():
    start, stop = MSR_READ, HID_WRITE + 8
    content = pad(start, stop-start)
    routines = {
        MSR_READ: (0x7C6000A6, 0x4E800020),
        MSR_WRITE: (0x7C600124, 0x4E800020),
        HID0_READ: (spr(3,1008,339), 0x4E800020),
        L2_READ: (spr(3,1017,339), 0x4E800020),
        L2_WRITE: (spr(3,1017,467), 0x4E800020),
        HID_READ: (spr(3,920,339), 0x4E800020),
        HID_WRITE: (spr(3,920,467), 0x4E800020),
    }
    for address, opcodes in routines.items():
        data = struct.pack('>'+('I'*len(opcodes)), *opcodes)
        content[address-start:address-start+len(data)] = data
    return bytes(content)


def synthetic_cache():
    # Independent original-free cache-control smoke: not the Undercover body.
    pc = CACHE
    ops = []
    def emit(w):
        ops.append(w)
    def call(target):
        emit(struct.unpack('>I', bl(pc+4*len(ops),target))[0])
    for x in (0x9421fff0,0x7c0802a6,0x90010014): emit(x)
    call(MSR_READ)
    emit(0x7c7e1b78)  # mr r30,r3
    call(HID0_READ)
    call(IC_ENABLE)
    call(DC_ENABLE)
    call(L2_READ)
    emit(0x64638000)  # oris r3,r3,0x8000
    call(L2_WRITE)
    call(L2_READ)
    emit(0x7fc3f378)  # mr r3,r30
    call(MSR_WRITE)
    call(DEBUG_PRINT)
    emit(0x38600001)  # li r3,1 for synthetic OSSetErrorHandler
    call(ERROR_HANDLER)
    for x in (0x80010014,0x7c0803a6,0x38210010,0x4e800020): emit(x)
    return struct.pack('>'+'I'*len(ops),*ops)


def bl_targets(body, start):
    result=[]
    for i,(w,) in enumerate(struct.iter_unpack('>I',body)):
        if w>>26 == 18 and (w & 1):
            result.append(linked_target(w,start+4*i))
    return result


def validate_original(cache, helpers):
    if len(cache) != CACHE_BYTES or struct.unpack_from('>I',cache,CACHE_BYTES-4)[0] != 0x4e800020:
        raise ValueError('original cache initializer span is incomplete')
    from audit_hardware_v17 import analyze
    counts, edges=analyze(cache,CACHE)
    if counts['direct_bl'] != 26 or counts['conditional_branches']!=5 or counts['sync']!=6:
        raise ValueError('original __OSCacheInit instruction census changed')
    permitted={HID0_READ,IC_ENABLE,DC_ENABLE,L2_READ,L2_WRITE,MSR_READ,MSR_WRITE,DEBUG_PRINT,ERROR_HANDLER}
    if not set(target for _,target in edges)<=permitted:
        raise ValueError('original __OSCacheInit calls an unknown target')
    for target in (IC_ENABLE,DC_ENABLE,L2_READ,L2_WRITE,MSR_READ,MSR_WRITE,DEBUG_PRINT,ERROR_HANDLER):
        if target not in [b for _,b in edges]:
            raise ValueError('missing original cache service call target')
    expected={MSR_READ:83,MSR_WRITE:146,HID0_READ:339,L2_READ:339,L2_WRITE:467}
    for addr,xo in expected.items():
        w=struct.unpack_from('>I', helpers, addr-MSR_READ)[0]
        if w>>26!=31 or ((w>>1)&1023)!=xo:
            raise ValueError('cache helper opcode does not match expected PPC SPR/MSR form')
        if addr in (HID0_READ,L2_READ,L2_WRITE):
            n=(((w>>11)&31)<<5)|((w>>16)&31)
            if n != (1008 if addr==HID0_READ else 1017):
                raise ValueError('cache helper SPR number changed')
    if not all(struct.unpack_from('>I',helpers,addr-MSR_READ+4)[0]==0x4e800020 for addr in expected):
        raise ValueError('cache helper lacks complete return')


def make(owner:Path|None):
    v19=make_v19(owner)
    previous=[]
    for i in range(6):
        file_pos,addr,size=[struct.unpack_from('>I',v19,base+i*4)[0] for base in (0,0x48,0x90)]
        previous.append((addr,v19[file_pos:file_pos+size]))
    if owner is not None:
        source=owner.read_bytes()
        if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
            raise ValueError('original game SHA-256 mismatch')
        helpers=bytearray(pad(MSR_READ,HID_WRITE+8-MSR_READ))
        for address in (MSR_READ,MSR_WRITE,HID0_READ,L2_READ,L2_WRITE):
            helpers[address-MSR_READ:address-MSR_READ+8]=get_text(source,address,8)
        helpers[HID_READ-MSR_READ:HID_READ-MSR_READ+16]=get_text(source,HID_READ,16)
        cache=get_text(source,CACHE,CACHE_BYTES)
        validate_original(cache,helpers)
    else:
        helpers=synthetic_helper_region()
        cache=synthetic_cache()
    # Keep original ICFlashInvalidate but replace direct IC/DC enable bodies with
    # deliberately synthetic syscall boundaries. These are NOT native OS ports.
    ic_region=pad(DC_ENABLE,IC_ENABLE+len(STOP)-DC_ENABLE)
    ic_region[:len(STOP)]=STOP
    ic_region[IC-DC_ENABLE:IC-DC_ENABLE+len(previous[3][1])]=previous[3][1]
    ic_region[IC_ENABLE-DC_ENABLE:IC_ENABLE-DC_ENABLE+len(STOP)]=STOP
    cache_region=pad(CACHE,ERROR_HANDLER+len(STOP)-CACHE)
    cache_region[:len(cache)]=cache
    cache_region[ERROR_HANDLER-CACHE:ERROR_HANDLER-CACHE+len(STOP)]=STOP
    sections=[previous[0],previous[1],(MSR_READ,bytes(helpers)),
              (DC_ENABLE,bytes(ic_region)),previous[4],(CACHE,bytes(cache_region)),
              (DEBUG_PRINT,STOP)]
    assert len(sections)==7
    total=256+sum((len(content)+3)&~3 for _,content in sections)
    result=bytearray(total)
    pos=256
    for i,(addr,body) in enumerate(sections):
        for base,value in ((0,pos),(0x48,addr),(0x90,len(body))):
            struct.pack_into('>I',result,base+4*i,value)
        result[pos:pos+len(body)]=body
        pos+=(len(body)+3)&~3
    struct.pack_into('>I',result,0xe0,0x8000403c)
    return bytes(result)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--owner-dol',type=Path,default=None)
    a=parser.parse_args()
    if a.output.exists():
        parser.error('refusing to overwrite private DOL slice')
    b=make(a.owner_dol)
    a.output.write_bytes(b)
    print('V20 bounded seven-section DOL created',len(b),'owner',bool(a.owner_dol))
