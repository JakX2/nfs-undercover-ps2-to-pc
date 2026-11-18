#!/usr/bin/env python3
"""Restore original OSSleepThread; stop at actual SelectThread entry."""
import argparse,struct
from pathlib import Path
from make_start_to_ipc_submit_v72 import make as previous,STOP as SLEEP
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x80529718
SIZE=0xec
EDGES=((0x8052a448,0x805265ac),(0x8052a4f8,STOP),(0x8052a500,0x805265d4))
def make(owner):
    old=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V73 original sleep edge differs")
    body=text_at(raw,SLEEP,SIZE)
    if word(body,SIZE-4)!=BLR:raise ValueError("V73 original sleep return differs")
    replace(old,SLEEP,struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(SIZE//4-2),body)
    replace(old,STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V73 private original thread sleep fixture")
