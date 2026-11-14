#!/usr/bin/env python3
"""V31 bounded SHA-pinned original Wii OSInit low-memory boot handoff.

Extract and validate instructions from the owner-private DOL only. No original
PowerPC text, game-derived generated code, or assets are included in this tool.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_hid4_v30 import make as make_v30, OSINIT, STOP as PREV_STOP, OSREPORT, be32
from make_osinit_execparams_v28 import text_at, target, SC, BLR

STOP = 0x80520778
LOWMEM = 0x80000000
BOOT_PTR_OFFSET = 0xF4
ARENA_HINT_OFFSET = 0x310C
FALLBACK_FLAG_OFFSET = 0x34


def validate(continuation):
    if len(continuation) != STOP - PREV_STOP:
        raise ValueError('incorrect source continuation length')
    # Recognize the unmodified original path, including all three intra-block
    # branches and the write/read opcode classes. Fail closed on other owners.
    for at, destination in ((0x80520740, 0x80520768),):
        if target(be32(continuation,at-PREV_STOP),at,False) != destination:
            raise ValueError('source low-memory direct branch changed')
    for at, dest in ((0x8052071c,0x80520744),
                     (0x8052074c,0x80520768)):
        opcode=be32(continuation,at-PREV_STOP)
        if opcode>>26 != 16:
            raise ValueError('source low-memory conditional branch opcode changed')
        delta=opcode&0xFFFC
        if delta&0x8000:delta-=0x10000
        if at+delta != dest or opcode&3:
            raise ValueError('source low-memory conditional branch changed')
    for at,klass in ((0x80520708,36),(0x8052070c,36),(0x80520710,36),
                     (0x80520714,32),(0x80520724,36),(0x80520728,32),
                     (0x8052072c,36),(0x80520730,32),(0x80520734,38),(0x80520738,32),
                     (0x8052073c,38),(0x80520744,32),(0x80520750,34),
                     (0x80520758,36),(0x8052075c,36),(0x80520760,34),
                     (0x80520764,36),(0x80520770,36),(0x80520774,32)):
        if be32(continuation,at-PREV_STOP)>>26 != klass:
            raise ValueError(f'source low-memory load/store changed at {at:08x}')
    # Pin offset, destination and base-register fields of memory accesses,
    # not only their major opcodes. All values are generic PPC addressing.
    fields={
        0x80520708:(4,13,-3512),0x8052070c:(0,13,-3516),
        0x80520710:(0,13,-16864),0x80520714:(5,4,0xF4),
        0x80520724:(3,13,-3516),0x80520728:(0,5,36),
        0x8052072c:(0,13,-3216),0x80520730:(0,5,12),0x80520734:(0,4,0x30E8),
        0x80520738:(0,13,-3216),0x8052073c:(0,4,0x30E9),
        0x80520744:(0,4,0x34),0x80520750:(3,4,0x30E8),
        0x80520758:(3,13,-3520),0x8052075c:(0,13,-3516),
        0x80520760:(0,4,0x30E9),0x80520764:(0,13,-3216),
        0x80520770:(0,13,-16864),0x80520774:(3,4,0x310C),
    }
    for at,(rt,ra,offset) in fields.items():
        op=be32(continuation,at-PREV_STOP)
        disp=op&0xffff
        if disp&0x8000:disp-=0x10000
        if ((op>>21)&31,(op>>16)&31,disp)!=(rt,ra,offset):
            raise ValueError(f'changed original Wii memory operand at {at:08x}')


def make(owner):
    original = make_v30(owner)  # includes SHA, original hardware/callgraph checks
    source = Path(owner).read_bytes()
    continuation = text_at(source, PREV_STOP, STOP-PREV_STOP)
    validate(continuation)
    sections=[]
    for i in range(7):
        off,addr,size=(be32(original,base+4*i) for base in (0,0x48,0x90))
        if off<256 or not size or off+size>len(original):
            raise ValueError('V30 parent slice geometry invalid')
        sections.append((addr,bytearray(original[off:off+size])))
    if sections[0][0]!=OSINIT or be32(sections[0][1],PREV_STOP-OSINIT)!=SC or        be32(sections[0][1],OSREPORT-OSINIT)!=SC:
        raise ValueError('V30 bounded OSInit original parent changed')
    os_text=sections[0][1]
    os_text[PREV_STOP-OSINIT:STOP-OSINIT]=continuation
    struct.pack_into('>II',os_text,STOP-OSINIT,SC,BLR)
    sections[0]=(OSINIT,os_text)
    output=bytearray(256+sum((len(payload)+3)&~3 for _,payload in sections))
    pos=256
    for i,(addr,payload) in enumerate(sections):
        for base,value in ((0,pos),(0x48,addr),(0x90,len(payload))):
            struct.pack_into('>I',output,base+4*i,value)
        output[pos:pos+len(payload)]=payload
        pos+=(len(payload)+3)&~3
    struct.pack_into('>I',output,0xE0,OSINIT)
    return bytes(output)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('original_dol',type=Path)
    p.add_argument('output_private_dol',type=Path)
    a=p.parse_args()
    if a.output_private_dol.exists():p.error('refusing to overwrite private image')
    image=make(a.original_dol)
    a.output_private_dol.write_bytes(image)
    print('PASS: V31 SHA-verified private OSInit low-memory slice:',len(image),'bytes')
