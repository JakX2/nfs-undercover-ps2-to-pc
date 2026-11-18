#!/usr/bin/env python3
"""Restore original SelectThread and its context helpers; no IRQ handler stub."""
import argparse,struct
from pathlib import Path
from make_start_to_ipc_sleep_v73 import make as previous,STOP as SELECT
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

SPANS=((SELECT,0x228),(0x80522928,0xc),(0x80522934,0x80),(0x805229b4,0xd8))
EDGES=((0x80529744,0x80522928),(0x80529814,0x80522934),(0x8052985c,0x805228cc),
       (0x80529860,0x805265c0),(0x80529870,0x805265ac),(0x80529888,0x80522af4),
       (0x80529918,0x805228cc),(0x80529920,0x805229b4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V74 original scheduler edge differs")
    for pc,size in SPANS:
        body=text_at(raw,pc,size)
        expected=struct.pack(">I",NOP)*(size//4)
        if pc==SELECT:
            expected=struct.pack(">II",SC,BLR)+expected[8:]
            if word(body,size-4)!=BLR:raise ValueError("V74 original scheduler return differs")
        replace(old,pc,expected,body)
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V74 private original scheduler fixture")
