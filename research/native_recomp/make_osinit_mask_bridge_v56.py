#!/usr/bin/env python3
"""Owner-private original Wii OSInit -> IRQ mask-loop integration, no embedded PPC.

Restores authentic original instructions inside V53 synthetic NOP padding.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_irq_disable_v53 import make as make_v53, NEW_STOP as OLD_STOP
from make_osinit_interrupt_bridge_v51 import TIME_SECTION
from make_alarm_v47 import original_text, be32, call_target, SC, BLR
from make_setmask_v54 import ENTRY as SETMASK, STOP as SETMASK_END

NEW_STOP=0x805266AC
NOP=0x60000000


def make(owner:Path):
    inherited=bytearray(make_v53(owner))
    original=owner.read_bytes()
    continuation=original_text(original,OLD_STOP,NEW_STOP-OLD_STOP)
    maskbody=original_text(original,SETMASK,SETMASK_END-SETMASK)
    if (len(continuation)!=0x14 or len(maskbody)!=0x25c or
        call_target(continuation,0x805266a0,OLD_STOP)!=SETMASK or
        be32(maskbody,len(maskbody)-4)!=BLR):
        raise ValueError('original Wii IRQ mask-loop callgraph or function return changed')
    offset,base,size=(be32(inherited,pos+4) for pos in (0,0x48,0x90))
    if base!=TIME_SECTION or offset<0x100 or offset+size>len(inherited):
        raise ValueError('V56 inherited time section geometry changed')
    position=offset+OLD_STOP-TIME_SECTION
    if (be32(inherited,position)!=SC or be32(inherited,position+4)!=BLR or
        any(be32(inherited,position+i)!=NOP for i in range(8,len(continuation)+8,4))):
        raise ValueError('refusing to overwrite non-synthetic inherited IRQ loop instructions')
    mask_at=offset+SETMASK-TIME_SECTION
    if (mask_at<offset or mask_at+len(maskbody)>offset+size or
        any(be32(inherited,mask_at+i)!=NOP for i in range(0,len(maskbody),4))):
        raise ValueError('refusing to overwrite original or non-NOP SetInterruptMask region')
    inherited[position:position+len(continuation)]=continuation
    struct.pack_into('>II',inherited,offset+NEW_STOP-TIME_SECTION,SC,BLR)
    inherited[mask_at:mask_at+len(maskbody)]=maskbody
    return bytes(inherited)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('original_owner_dol',type=Path)
    p.add_argument('private_output',type=Path)
    a=p.parse_args()
    if a.private_output.exists():p.error('refusing to overwrite private image')
    a.private_output.write_bytes(make(a.original_owner_dol))
    print('PASS: V56 SHA-pinned original OSInit interrupt loop restored privately')
