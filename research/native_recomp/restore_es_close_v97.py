#!/usr/bin/env python3
"""V97 owner-local exact original ES close wrapper and IOS_Close."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_directory_v96 import (restore as v96,ROOT as V96_ROOT,SIZE as V96_SIZE,
    v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,
    v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
SPANS=((0x804f063c,0x48),(0x80519b24,0xa8))
EDGES=((0x804f0658,0x80519b24),(0x80519b5c,0x8051ad38),(0x80519ba8,0x805195ec))
def restore(old,bodies):
    if set(bodies)!=set(pc for pc,n in SPANS):raise ValueError("V97 exact body set differs")
    for pc,n in SPANS:
        if len(bodies[pc])!=n or be32(bodies[pc],n-4)!=BLR:raise ValueError("V97 original close geometry differs")
    for pc,dst in EDGES:
        base=next(a for a,n in SPANS if a<=pc<a+n)
        if target(be32(bodies[base],pc-base),pc,True)!=dst:raise ValueError("V97 direct edge differs")
    out=bytearray(old)
    for pc,n in SPANS:
        before=STUB+NOP*(n//4-2) if pc==SPANS[0][0] else NOP*(n//4)
        replace(out,pc,before,bodies[pc])
    reverse=bytearray(out)
    for pc,n in SPANS:
        before=STUB+NOP*(n//4-2) if pc==SPANS[0][0] else NOP*(n//4)
        replace(reverse,pc,bodies[pc],before)
    if bytes(reverse)!=old or old[:256]!=out[:256]:raise ValueError("V97 unrelated private mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    raw=a.owner.read_bytes();old=a.fixture.read_bytes()
    x=v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))
    x=v89(x,text_at(raw,OS_CALL,4),text_at(raw,V89_ROOT,V89_SIZE))
    x=v91(x,{pc:text_at(raw,pc,n) for pc,n in V91_SPANS})
    x=v93(x,text_at(raw,V93_ROOT,V93_SIZE))
    x=v94(x,text_at(raw,V94_ROOT,V94_SIZE))
    x=v95(x,{pc:text_at(raw,pc,n) for pc,n in V95_SPANS})
    x=v96(x,text_at(raw,V96_ROOT,V96_SIZE))
    if x!=old:raise ValueError("V97 inherited authenticated V96 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,{pc:text_at(raw,pc,n) for pc,n in SPANS}))
    print("PASS: V97 original ES close bodies restored privately")
if __name__=="__main__":main()
