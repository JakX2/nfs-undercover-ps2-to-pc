#!/usr/bin/env python3
"""V70 authentic STM call path; nonreturning test-only IOS boundary."""
import argparse,struct
from pathlib import Path
from make_start_to_ipc_client_v69 import make as previous,STOP as OLD
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

STM=0x8052b034
STM_SIZE=0x118
OPEN=0x80519944
IOCTL=0x8051a1a4
STOP=OPEN
OS_STOP=0x80520968
SKIP=0x8052097c
EDGES=((0x80520964,STM),(0x8052b08c,OPEN),(0x8052b0b4,OPEN),
       (0x8052b0d0,0x805265ac),(0x8052b104,IOCTL),(0x8052b124,0x805265d4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V70 authentic STM call graph differs")
    for pc in (0x80520954,0x80520960):
        op=word(text_at(raw,pc,4),0)
        disp=op&0xfffc
        if disp&0x8000:disp-=0x10000
        if op>>26!=16 or op&2 or pc+disp!=SKIP:raise ValueError("V70 original OSInit alternate target differs")
    stm=text_at(raw,STM,STM_SIZE)
    if word(stm,STM_SIZE-4)!=BLR:raise ValueError("V70 STM original return differs")
    replace(old,STM,struct.pack(">I",NOP)*(STM_SIZE//4),stm)
    for pc in (OPEN,IOCTL,SKIP):
        replace(old,pc,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    n=OS_STOP-OLD
    replace(old,OLD,struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(n//4),
            text_at(raw,OLD,n)+struct.pack(">II",SC,BLR))
    return bytes(old)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    data=make(a.owner)
    with a.output.open("xb") as f:f.write(data)
    print("PASS: V70 private STM fixture")
