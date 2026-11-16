#!/usr/bin/env python3
"""Build an owner-private original OSInit→system-call integration test image.

All original PowerPC and syscall-vector words are extracted from the pinned
owner's Wii DOL. Only test-only DBPrintf callbacks and end stops are synthetic.
The original game's complete OSInit is NOT claimed by this bounded image.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_vectors_v44 import make as make_v44
from make_osinit_execparams_v28 import text_at, target, SC, BLR, NOP
from make_osinit_systemcall_v45 import SOURCE, ENTRY, END, FLUSH, INVALIDATE

OSINIT = 0x80520670
GETTIME = 0x8052A824
SAVE = 0x805450E8
RESTORE = 0x80545134
RESTORE_END = 0x80545168
EXCEPTION_RETURN_START = 0x80520E58
EXCEPTION_RETURN_END = 0x80520E74
DEBUG_PRINT = 0x804E50B8
MARK = 0x804E50A0
OLD_OSINIT_STOP = 0x805208AC
NEW_OSINIT_STOP = 0x805208B0


def be32(data, i):
    return struct.unpack_from('>I', data, i)[0]


def make(owner: Path):
    image = bytearray(make_v44(owner))  # original DOL SHA and ancestor checks
    original = owner.read_bytes()
    sections = []
    for i in range(7):
        off, addr, size = (be32(image,base+i*4) for base in (0,0x48,0x90))
        if off<256 or size<=0 or off+size>len(image):
            raise ValueError('malformed V44 test section')
        sections.append([addr, bytearray(image[off:off+size])])
    if [sections[j][0] for j in (0,1,3,6)] != [OSINIT,GETTIME,SAVE,MARK]:
        raise ValueError('unexpected inherited V44 test geometry')
    dataoff, dataaddr, datasize = (be32(image,n) for n in (0x1c,0x64,0xac))
    if dataoff<256 or datasize!=0x98 or dataoff+datasize>len(image):
        raise ValueError('original exception template data section missing')
    template = bytes(image[dataoff:dataoff+datasize])
    first = sections[0][1]
    def first_word(pc):return be32(first,pc-OSINIT)
    if (first_word(OLD_OSINIT_STOP),first_word(OLD_OSINIT_STOP+4),
        first_word(EXCEPTION_RETURN_START),first_word(EXCEPTION_RETURN_START+4))!=(SC,BLR,SC,BLR):
        raise ValueError('V44 original OSInit or exception debug stop changed')
    if first_word(NEW_OSINIT_STOP+4)!=NOP:
        raise ValueError('next service synthetic boundary conflicts with original code')
    # Original OSExceptionInit epilogue contains original calls to DBPrintf and
    # _restgpr_20; only the DBPrintf function itself is a synthetic callback.
    tail=text_at(original,EXCEPTION_RETURN_START,EXCEPTION_RETURN_END-EXCEPTION_RETURN_START)
    branch=text_at(original,OLD_OSINIT_STOP,4)
    if (target(be32(tail,0),EXCEPTION_RETURN_START,True)!=DEBUG_PRINT or
        target(be32(tail,8),EXCEPTION_RETURN_START+8,True)!=RESTORE or
        target(be32(branch,0),OLD_OSINIT_STOP,True)!=ENTRY or
        be32(tail,len(tail)-4)!=BLR):
        raise ValueError('original exception return and system-call branch changed')
    first[EXCEPTION_RETURN_START-OSINIT:EXCEPTION_RETURN_END-OSINIT]=tail
    struct.pack_into('>I',first,OLD_OSINIT_STOP-OSINIT,be32(branch,0))
    struct.pack_into('>II',first,NEW_OSINIT_STOP-OSINIT,SC,BLR)
    # The original system-call handler source begins 0x1780 bytes before the
    # existing GETTIME helper section; synthetic NOPs bridge only unexecuted
    # address space. Original function and handler bytes retain their PCs.
    source_to_end=text_at(original,SOURCE,END-SOURCE)
    original_time=sections[1][1]
    gap=GETTIME-SOURCE
    if gap < len(source_to_end) or gap%4:
        raise ValueError('cannot extend owner-private GETTIME test segment')
    merged=bytearray(NOP.to_bytes(4,'big')*(gap//4))
    merged[0:len(source_to_end)]=source_to_end
    merged.extend(original_time)
    sections[1]=[SOURCE,merged]
    # The original save and restore register thunks are kept at their real
    # instruction addresses, filling the unused 24-byte gap only with NOPs.
    restore=text_at(original,RESTORE,RESTORE_END-RESTORE)
    old_save=sections[3][1]
    missing=RESTORE-(SAVE+len(old_save))
    if missing<0 or missing%4 or be32(restore,len(restore)-4)!=BLR:
        raise ValueError('original restore thunk overlaps inherited save thunk')
    old_save.extend(NOP.to_bytes(4,'big')*(missing//4))
    old_save.extend(restore)
    # Test-only DBPrintf stub. The real debug service remains unresolved.
    if MARK+len(sections[6][1])!=DEBUG_PRINT:
        raise ValueError('DBPrintf stub is not adjacent to original marker body')
    sections[6][1].extend(struct.pack('>II',SC,BLR))
    output=bytearray(256+sum(len(s) for _,s in sections)+len(template))
    p=256
    for i,(guest,code) in enumerate(sections):
        for base,value in ((0,p),(0x48,guest),(0x90,len(code))):
            struct.pack_into('>I',output,base+4*i,value)
        output[p:p+len(code)]=code
        p+=len(code)
    for base,value in ((0x1c,p),(0x64,dataaddr),(0xac,len(template))):
        struct.pack_into('>I',output,base,value)
    output[p:p+len(template)]=template
    struct.pack_into('>I',output,0xE0,OSINIT)
    return bytes(output)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('original_owner_dol',type=Path)
    p.add_argument('private_output_dol',type=Path)
    a=p.parse_args()
    if a.private_output_dol.exists():p.error('refusing overwrite of private DOL')
    a.private_output_dol.write_bytes(make(a.original_owner_dol))
    print('PASS: V46 original OSInit→syscall private integration test DOL built')
