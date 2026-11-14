#!/usr/bin/env python3
"""Produce a bounded owner-private DOL with real __start -> DBInit -> OSInit edge.

Original instructions are read exclusively from the supplied SHA-pinned DOL.
The OSInit entry is a synthetic test-only stop. Unsafe firmware boot modes
have synthetic syscall guards; the ordinary zero-flag boot path remains real.
Do not commit the output DOL or NWiiRecomp-generated game C++.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_start_to_data_v23 import make as make_v23, START, RETURN_PC, SC, BLR, NOP
from make_hardware_boundary_v17 import get_text, ORIGINAL_SHA, linked_target

DBINIT = 0x804E5020
DBPRINTF = 0x804E50B8
OSINIT = 0x80520670
PSINIT = 0x80520FB4
BOOT_END = 0x80004160
SYNTH_MARKER = 0x80037000

def be32(b, pos):
    return struct.unpack_from('>I', b, pos)[0]


def synth_dbinit():
    # Independent synthetic code: lis r9,0x8003; li r10,0x55aa;
    # stw r10,0x7000(r9); blr
    return struct.pack('>4I', 0x3D208003, 0x394055AA, 0x91497000, BLR)


def make(owner):
    base = make_v23(owner)
    src = None
    if owner is not None:
        src = owner.read_bytes()
        if hashlib.sha256(src).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner DOL SHA mismatch')
    sections = []
    for i in range(7):
        off, addr, count = [be32(base, head + 4*i) for head in (0,0x48,0x90)]
        if off < 256 or count == 0 or off + count > len(base):
            raise ValueError('V23 base section missing/truncated')
        sections.append((addr, bytearray(base[off:off + count])))
    if sections[0][0] != START or sections[1][0] != PSINIT or sections[6][0] != DBPRINTF:
        raise ValueError('unexpected V23 code section layout')
    start = sections[0][1]
    if be32(start,RETURN_PC-START) != SC:
        raise ValueError('V23 stop missing')
    if src is not None:
        tail = get_text(src,RETURN_PC,BOOT_END-RETURN_PC)
        if linked_target(be32(tail,0x80004158-RETURN_PC),0x80004158)!=DBINIT:
            raise ValueError('original DBInit call target wrong')
        if linked_target(be32(tail,0x8000415C-RETURN_PC),0x8000415C)!=OSINIT:
            raise ValueError('original OSInit call target wrong')
        start[RETURN_PC-START:BOOT_END-START]=tail
        # Deliberate test-only guards on alternative firmware path. The zero
        # low-memory flags select the unmodified original startup instructions.
        for pc in (0x800040C8,0x800040DC):
            start[pc-START:pc-START+4]=SC.to_bytes(4,'big')
        start[BOOT_END-START:BOOT_END-START+4]=BLR.to_bytes(4,'big')
    else:
        # Different independent branch instructions for the synthetic test.
        # Parent returns from synthetic data init, calls our distinct synthetic
        # DBInit, and reaches the test-only OSInit stop.
        def bl(pc,target):
            displacement=(target-pc)&0x03FFFFFC
            return 0x48000001 | displacement
        start[RETURN_PC-START:RETURN_PC-START+12]=struct.pack('>3I',
            bl(RETURN_PC,DBINIT), bl(RETURN_PC+4,OSINIT), BLR)
    sections[0]=(START,start)
    ps=sections[1][1]
    expanded=bytearray(NOP.to_bytes(4,'big')*((PSINIT-OSINIT+len(ps)+3)//4))
    expanded[PSINIT-OSINIT:PSINIT-OSINIT+len(ps)]=ps
    expanded[0:8]=struct.pack('>2I', SC,BLR)
    sections[1]=(OSINIT,expanded)
    db=sections[6][1]
    dbexpanded=bytearray(NOP.to_bytes(4,'big')*((DBPRINTF-DBINIT+len(db)+3)//4))
    dbexpanded[DBPRINTF-DBINIT:DBPRINTF-DBINIT+len(db)]=db
    dbfunc=get_text(src,DBINIT,40) if src is not None else synth_dbinit()
    if src is not None and (len(dbfunc)!=40 or be32(dbfunc,36)!=BLR):
        raise ValueError('original DBInit body missing full return')
    dbexpanded[:len(dbfunc)]=dbfunc
    sections[6]=(DBINIT,dbexpanded)
    data_offset=be32(base,0x1c)
    data_len=be32(base,0xac)
    if be32(base,0x64)!=0x80006420 or data_len!=0xb0 or data_offset+data_len>len(base):
        raise ValueError('missing V23 init-data table')
    table=base[data_offset:data_offset+data_len]
    result=bytearray(256+sum((len(v)+3)&~3 for _,v in sections)+len(table))
    position=256
    for i,(address,payload) in enumerate(sections):
        for off,val in ((0,position),(0x48,address),(0x90,len(payload))):
            struct.pack_into('>I',result,off+4*i,val)
        result[position:position+len(payload)]=payload
        position+=(len(payload)+3)&~3
    for off,val in ((0x1c,position),(0x64,0x80006420),(0xac,len(table))):
        struct.pack_into('>I',result,off,val)
    result[position:position+len(table)]=table
    struct.pack_into('>I',result,0xe0,START)
    return bytes(result)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('output',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    if args.output.exists():
        ap.error('refusing overwrite')
    output=make(args.owner_dol)
    args.output.write_bytes(output)
    print('Private V24 start-to-DBInit image:',len(output),'bytes; original='+str(bool(args.owner_dol)))
