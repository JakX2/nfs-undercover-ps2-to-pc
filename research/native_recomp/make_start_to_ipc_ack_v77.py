#!/usr/bin/env python3
"""Restore the original registered IPC handler and all direct dependencies."""
import argparse,struct
from pathlib import Path
from make_start_to_irq_dispatch_v76 import make as previous,STOP as IPC
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
STOP=0x80529434
SPANS=((IPC,0x1ac),(0x805190c0,0x258),(0x8051b060,0x10),(0x8051b070,0x7c),(0x8052a51c,0xf4))
EDGES=((0x80519338,0x8051905c),(0x80519350,0x805190c0),(0x80519358,0x8051905c),
       (0x8051936c,0x8051905c),(0x8051937c,0x8051906c),(0x805193a0,0x8051b060),
       (0x805193d0,0x8052a51c),(0x805193d8,0x8051905c),(0x805193e8,0x8051906c),
       (0x80519460,0x8051906c),(0x80519498,0x8051905c),(0x805194a8,0x8051906c),
       (0x805192d0,0x8052a51c),(0x805192f4,0x8051b070),
       (0x8052a534,0x805265ac),(0x8052a5ec,0x80529718),(0x8052a5f4,0x805265d4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V77 IPC handler dependency differs")
    for pc,size in SPANS:
        expected=struct.pack(">I",NOP)*(size//4)
        if pc==IPC:expected=struct.pack(">II",SC,BLR)+expected[8:]
        replace(old,pc,expected,text_at(raw,pc,size))
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V77 private original IPC handler fixture")
