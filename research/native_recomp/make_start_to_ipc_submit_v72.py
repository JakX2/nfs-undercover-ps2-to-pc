#!/usr/bin/env python3
"""Restore synchronous IPC request submission; stop before guest scheduling."""
import argparse,struct
from pathlib import Path
from make_start_to_ios_open_v71 import make as previous,STOP as SUBMIT
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

STOP=0x8052a430
SPANS=((SUBMIT,0x240),(0x805293b0,0x10),(0x8051afe0,0x80),
       (0x8051ad3c,0x1ec),(0x8051905c,0x10))
EDGES=((0x8051962c,0x805293b0),(0x80519638,0x805222c0),(0x8051963c,0x805265ac),
       (0x805196d0,0x8051afe0),(0x805196e0,0x805265d4),(0x805196f4,0x8051ad3c),
       (0x8051977c,0x8051906c),(0x805197b4,0x8051905c),(0x805197c4,0x8051906c),
       (0x805197d4,STOP),(0x805197dc,0x805265d4),(0x80519804,0x8051ad3c),
       (0x8051ad60,0x805265ac),(0x8051af04,0x805265d4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V72 original submission edge differs")
    for pc,size in SPANS:
        original=text_at(raw,pc,size)
        if word(original,size-4)!=BLR:raise ValueError("V72 original submission return differs")
        expected=struct.pack(">I",NOP)*(size//4)
        if pc==SUBMIT:expected=struct.pack(">II",SC,BLR)+expected[8:]
        replace(old,pc,expected,original)
    replace(old,STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V72 private original IPC submission fixture")
