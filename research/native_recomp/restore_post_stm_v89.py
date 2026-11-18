#!/usr/bin/env python3
"""V89 owner-local original next OSInit subsystem fixture extension."""
import argparse
import struct
from pathlib import Path
from make_osinit_execparams_v28 import SC, BLR, NOP, text_at, be32, target
from make_start_to_irq_enable_v68 import replace
from restore_stm_ioctl_v86 import restore as restore_v86, IOCTL, SIZE as IOCTL_SIZE
from make_start_to_ipc_ack_v77 import make as make_v77

OS_CALL=0x80520968
ROOT=0x8052f790
SIZE=0xa0
EDGES=((0x8052f7a0,0x805265ac),(0x8052f7b0,0x805265d4),(0x8052f7c4,0x805265d4),
       (0x8052f7cc,0x80521018),(0x8052f7d8,0x805293b0),(0x8052f7dc,0x8051fd44),
       (0x8052f7ec,0x8051e7e4),(0x8052f808,0x8052f94c))
BOUNDARIES=(0x8051e7e4,0x8052f94c)
OLD_OS=struct.pack(">III",SC,BLR,NOP)
STUB=struct.pack(">II",SC,BLR)
EMPTY=struct.pack(">I",NOP)

def restore(fixture,call,body):
    if len(call)!=4 or target(be32(call,0),OS_CALL,True)!=ROOT:
        raise ValueError("V89 original OSInit edge differs")
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR:
        raise ValueError("V89 original subsystem span differs")
    for pc,dest in EDGES:
        if target(be32(body,pc-ROOT),pc,True)!=dest:
            raise ValueError("V89 original subsystem dependency differs")
    patches=[(OS_CALL,OLD_OS,call+STUB),(ROOT,EMPTY*(SIZE//4),body)]
    patches.extend((pc,EMPTY*2,STUB) for pc in BOUNDARIES)
    result=bytearray(fixture)
    for pc,old,new in patches:
        replace(result,pc,old,new)
    reverse=bytearray(result)
    for pc,old,new in reversed(patches):
        replace(reverse,pc,new,old)
    if bytes(reverse)!=fixture or result[:256]!=fixture[:256]:
        raise ValueError("V89 unexpected fixture mutation")
    return bytes(result)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path)
    p.add_argument("owner",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("refusing private overwrite")
    raw=a.owner.read_bytes()
    old=a.fixture.read_bytes()
    if restore_v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))!=old:
        raise ValueError("V89 inherited fixture does not match authenticated V86 geometry")
    result=restore(old,text_at(raw,OS_CALL,4),text_at(raw,ROOT,SIZE))
    with a.output.open("xb") as f:
        f.write(result)
    print("PASS: V89 exact owner-local next OSInit subsystem fixture")

if __name__=="__main__":
    main()
