#!/usr/bin/env python3
"""V71 restore original IOS_Open; stop explicitly at its submission helper."""
import argparse,struct
from pathlib import Path
from make_start_to_stm_v70 import make as previous,OPEN
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
SIZE=0x120
PROFILE=0x8051ad38
STOP=0x805195ec
EDGES=((0x80519988,PROFILE),(0x80519a18,0x805222c0),(0x80519a38,STOP))
def make(owner):
    private=bytearray(previous(owner));raw=owner.read_bytes()
    for pc,dst in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dst:raise ValueError("V71 original IOS_Open call edge changed")
    original=text_at(raw,OPEN,SIZE)
    returns=[i for i in range(0,SIZE,4) if word(original,i)==BLR]
    if len(returns)!=1 or returns[0]<0xf4:
        raise ValueError("V71 original IOS_Open return geometry changed")
    if word(text_at(raw,PROFILE,4),0)!=BLR:
        raise ValueError("V71 original profiling leaf is not BLR")
    replace(private,OPEN,struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(SIZE//4-2),original)
    replace(private,PROFILE,struct.pack(">I",NOP),text_at(raw,PROFILE,4))
    replace(private,STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    return bytes(private)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    data=make(a.owner)
    with a.output.open("xb") as f:f.write(data)
    print("PASS: V71 private original IOS_Open fixture")
