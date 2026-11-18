#!/usr/bin/env python3
"""Restore actual original external IRQ trampoline and dispatcher."""
import argparse,struct
from pathlib import Path
from make_start_to_external_vector_v75 import make as previous,STOP as TRAMPOLINE
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
STOP=0x80519318
DISPATCH=0x80526a3c
SPANS=((TRAMPOLINE,0x50),(DISPATCH,0x2a4),(0x805293f8,0x3c),(0x80529434,0x3c),(0x80529940,0x18))
EDGES=((0x80526a78,0x805229b4),(0x80526c80,0x8052a824),(0x80526c94,0x805293f8),
       (0x80526cac,0x80529434),(0x80526cb0,0x80529940),(0x80526cb8,0x805229b4),(0x80526cc0,0x805229b4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V76 dispatcher call edge differs")
    site=0x80526d2c;op=struct.unpack(">I",text_at(raw,site,4))[0]
    disp=((op&0x03fffffc)^0x02000000)-0x02000000
    if op>>26!=18 or op&3 or site+disp!=DISPATCH:raise ValueError("V76 trampoline tail differs")
    for pc,size in SPANS:
        expected=struct.pack(">I",NOP)*(size//4)
        if pc==TRAMPOLINE:expected=struct.pack(">II",SC,BLR)+expected[8:]
        replace(old,pc,expected,text_at(raw,pc,size))
    replace(old,STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V76 private original IRQ dispatcher fixture")
