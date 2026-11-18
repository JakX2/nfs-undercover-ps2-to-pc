#!/usr/bin/env python3
"""Owner-only extension from V67 to original interrupt-enable return.

The candidate callsite and leaf geometry are checked against the authenticated
DOL at run time. No original instruction bytes are embedded or exported.
"""
import argparse,struct
from pathlib import Path
from make_start_to_arena_clear_v67 import make as previous, STOP as OLD
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target

ENABLE=0x805265c0
STOP=OLD+4

def replace(raw,pc,expected,body):
    if len(expected)!=len(body) or len(body)%4:
        raise ValueError("V68 replacement geometry")
    matches=[]
    for i in range(7):
        off,base,size=(struct.unpack_from(">I",raw,k+4*i)[0] for k in (0,0x48,0x90))
        if off>=256 and off+size<=len(raw) and base<=pc and pc+len(body)<=base+size:
            matches.append(off+pc-base)
    if len(matches)!=1:raise ValueError("V68 range not uniquely mapped")
    at=matches[0]
    if raw[at:at+len(body)]!=expected:raise ValueError("V68 overlap with inherited text")
    raw[at:at+len(body)]=body

def make(owner):
    old=bytearray(previous(owner))
    raw=owner.read_bytes()
    call=text_at(raw,OLD,4)
    if call_target(call,OLD,OLD)!=ENABLE:raise ValueError("V68 candidate interrupt-enable call edge differs")
    leaf=text_at(raw,ENABLE,20)
    if struct.unpack_from(">I",leaf,16)[0]!=BLR:raise ValueError("V68 candidate leaf return differs")
    replace(old,ENABLE,struct.pack(">I",NOP)*5,leaf)
    replace(old,OLD,struct.pack(">III",SC,BLR,NOP),call+struct.pack(">II",SC,BLR))
    return bytes(old)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V68 private interrupt-enable fixture")
