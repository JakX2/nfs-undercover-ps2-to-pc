#!/usr/bin/env python3
"""V25 bounded startup: genuine OSInit prefix, register-save helper, synthetic OS time stop.

The owner original is SHA pinned by V24. Game bytes live only in owner-private
scratch DOLs and are not included in this independently authored script.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from make_start_to_dbinit_v24 import make as make_v24, DBINIT, OSINIT, be32
from make_start_to_data_v23 import SC, BLR, NOP
from make_hardware_boundary_v17 import get_text, ORIGINAL_SHA, linked_target

OS_TIME = 0x8052A844
SAVE20 = 0x805450E8
ALT_INIT = 0x80520BDC
CACHE_START = 0x80522540
SYNTH_MARKER = 0x80037004


def bl(pc, target):
    diff = target-pc
    if diff % 4 or not -(1 << 25) <= diff < (1 << 25):
        raise ValueError('PowerPC relative call out of bounds')
    return 0x48000001 | (diff & 0x03fffffc)


def synth_osinit():
    # Independently hand-authored PPC: stack frame -96; save LR; call helper;
    # mark guest memory; call time service. Different from original OSInit.
    return struct.pack('>9I',
        0x9421ffa0,  # stwu r1,-96(r1)
        0x7c0802a6,  # mflr r0
        0x90010064,  # stw r0,100(r1)
        0x39610060,  # addi r11,r1,96
        bl(OSINIT+0x10,SAVE20),
        0x3d208003,  # lis r9,0x8003
        0x39400707,  # li r10,0x707
        0x91497004,  # stw r10,0x7004(r9)
        bl(OSINIT+0x20,OS_TIME),
    )


def synth_save():
    # Separate synthetic helper writes a small register spill at r11-48.
    return struct.pack('>2I', 0x930bffd0, BLR)  # stw r24,-48(r11); blr


def make(owner):
    old = make_v24(owner)
    src = None
    if owner is not None:
        src = owner.read_bytes()
        if hashlib.sha256(src).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner original DOL SHA mismatch')
    sections = []
    for i in range(7):
        off, addr, length = (be32(old, base+i*4) for base in (0,0x48,0x90))
        if off < 256 or length == 0 or off + length > len(old):
            raise ValueError('V24 base section truncated')
        sections.append((addr,bytearray(old[off:off+length])))
    if sections[1][0] != OSINIT or sections[5][0] != CACHE_START:
        raise ValueError('unexpected parent DOL memory layout')
    os_addr, os_text = sections[1]
    # Original initial 15 PPC instructions end with BL to __OSGetSystemTime.
    if src is not None:
        prefix = get_text(src, OSINIT, 0x3c)
        if len(prefix) != 0x3c:
            raise ValueError('OSInit prefix truncated')
        if linked_target(be32(prefix, 0x10), OSINIT+0x10) != SAVE20:
            raise ValueError('original _savegpr_20 call changed')
        if linked_target(be32(prefix, 0x38), OSINIT+0x38) != OS_TIME:
            raise ValueError('original OS time call changed')
        if be32(prefix, 0x34) != 0x900df21c:
            raise ValueError('original one-time OS init flag store changed')
        helper = get_text(src,SAVE20,52)
        if len(helper) != 52 or be32(helper,48) != BLR:
            raise ValueError('original PowerPC register-save helper truncated')
    else:
        prefix = synth_osinit()
        helper = synth_save()
    os_text[:len(prefix)] = prefix
    os_text[len(prefix):len(prefix)+4] = struct.pack('>I',BLR)
    # Explicit rejection boundary for the "already initialized" conditional
    # branch. Never imply that the rest of OSInit is implemented.
    os_text[ALT_INIT-OSINIT:ALT_INIT-OSINIT+8] = struct.pack('>2I',SC,BLR)
    sections[1] = (os_addr, os_text)

    cache_addr, cache_text = sections[5]
    stop_end = SAVE20+len(helper)
    target_len = stop_end-CACHE_START
    if target_len <= len(cache_text) or target_len > 200000:
        raise ValueError('unexpected helper memory geometry')
    cache_text.extend(NOP.to_bytes(4,'big') * ((target_len-len(cache_text)+3)//4))
    at_time = OS_TIME-CACHE_START
    cache_text[at_time:at_time+8] = struct.pack('>2I',SC,BLR)
    at_save = SAVE20-CACHE_START
    cache_text[at_save:at_save+len(helper)] = helper
    sections[5] = (cache_addr,cache_text)
    data_off=be32(old,0x1c)
    data_len=be32(old,0xac)
    if data_len!=0xb0 or data_off+data_len>len(old):
        raise ValueError('V24 data table missing')
    data=old[data_off:data_off+data_len]
    output=bytearray(256 + sum((len(b)+3)&~3 for _,b in sections) + len(data))
    pos=256
    for i,(address,payload) in enumerate(sections):
        for base,value in ((0,pos),(0x48,address),(0x90,len(payload))):
            struct.pack_into('>I',output,base+4*i,value)
        output[pos:pos+len(payload)]=payload
        pos+=(len(payload)+3)&~3
    for base,value in ((0x1c,pos),(0x64,0x80006420),(0xac,len(data))):
        struct.pack_into('>I',output,base,value)
    output[pos:pos+len(data)]=data
    struct.pack_into('>I',output,0xe0,0x8000403c)
    return bytes(output)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('output',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    if args.output.exists():
        ap.error('refusing overwrite')
    image=make(args.owner_dol)
    args.output.write_bytes(image)
    print('V25 bounded OSInit prefix private image:',len(image),'bytes; owner='+str(bool(args.owner_dol)))
