#!/usr/bin/env python3
"""Build owner-private V40 OSInit exception-mark test image with authentic PPC helpers.

The original instructions are extracted solely from SHA-verified owner Wii DOL.
The resulting game-derived test image must never be committed or redistributed.
"""
from pathlib import Path
import argparse
import struct
from make_osinit_exception_v39 import make as make_v39, ENTRY, EXC_NORMAL_STOP as OLD_STOP
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import be32

MARK = 0x804E50A0
MARK_LENGTH = 24
FIRST_STOP = 0x80520CC8  # immediately after first original __DBIsExceptionMarked call
SECOND_STOP = 0x80520CF4 # immediately after second original __DBIsExceptionMarked call
EXEC = 0x80523B1C
OSINIT = 0x80520670
FILL = 0x60000000  # synthetic private-slice inter-section gap, never game code


def make(owner):
    base = make_v39(owner)
    original = Path(owner).read_bytes() # parent verifies owner SHA before any original code access
    body = text_at(original, OLD_STOP, SECOND_STOP - OLD_STOP)
    helper = text_at(original, MARK, MARK_LENGTH)
    if len(body)!=0x4c or len(helper)!=MARK_LENGTH or be32(helper,20)!=BLR:
        raise ValueError('original Wii exception mark helper or continuation length changed')
    for pc in (0x80520CC4,0x80520CF0):
        if target(be32(body,pc-OLD_STOP),pc,True)!=MARK:
            raise ValueError('exception branch no longer calls original __DBIsExceptionMarked')
    # Guard mutations to the original exception branch and marker routine.
    if be32(body,0)!=0x806DF244:
        raise ValueError('original exception state machine differs')
    pieces=[]
    for i in range(7):
        off,guest,size=[be32(base,where+4*i) for where in (0,0x48,0x90)]
        if off<256 or size<=0 or off+size>len(base):
            raise ValueError('invalid inherited test-image geometry')
        pieces.append((guest,bytearray(base[off:off+size])))
    if pieces[0][0]!=OSINIT or pieces[3][0]!=EXEC:
        raise ValueError('unexpected inherited OSInit / execparams layout')
    os = pieces[0][1]
    where=OLD_STOP-OSINIT
    if be32(os,where)!=SC:
        raise ValueError('missing V39 stop before first marking logic')
    os[where:where+len(body)]=body
    struct.pack_into('>II',os,FIRST_STOP-OSINIT,SC,BLR)
    struct.pack_into('>II',os,SECOND_STOP-OSINIT,SC,BLR)
    # Consolidate two adjacent guest sections; the 0xC14-byte bridge consists
    # entirely of synthetic NOPs, never game-derived PPC code.
    exebase,exe=pieces[3]
    os_end=OSINIT+len(os)
    if os_end>exebase or (exebase-os_end)%4:
        raise ValueError('unsafe original guest text section merge')
    merged=os + bytearray(struct.pack('>I',FILL)*((exebase-os_end)//4)) + exe
    assert len(merged)==exebase+len(exe)-OSINIT
    # The freed seventh section is the original, non-relocated debug helper.
    pieces=[(OSINIT,merged),pieces[1],pieces[2],pieces[4],pieces[5],pieces[6],(MARK,bytearray(helper))]
    out=bytearray(256+sum((len(chunk)+3)&~3 for _,chunk in pieces))
    cursor=256
    for i,(guest,chunk) in enumerate(pieces):
        for start,value in ((0,cursor),(0x48,guest),(0x90,len(chunk))):
            struct.pack_into('>I',out,start+4*i,value)
        out[cursor:cursor+len(chunk)]=chunk
        cursor+=(len(chunk)+3)&~3
    struct.pack_into('>I',out,0xe0,OSINIT)
    return bytes(out)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_dol',type=Path)
    ap.add_argument('destination',type=Path)
    args=ap.parse_args()
    if args.destination.exists():ap.error('refusing to overwrite existing owner-private DOL')
    args.destination.write_bytes(make(args.owner_dol))
    print('PASS: V40 owner-private exception mark native test DOL created')
