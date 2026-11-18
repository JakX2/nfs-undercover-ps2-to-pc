#!/usr/bin/env python3
"""Restore only owner-authenticated SC async wrapper and heap getter for V103."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_sc_path_v102 import (restore as v102,SPANS as V102_SPANS,
    v101,V101_ROOT,V101_SIZE,v100,V100_SPANS,v99,V99_ROOT,V99_SIZE,
    v97,V97_SPANS,v96,V96_ROOT,V96_SIZE,v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
SPANS=((0x804f1e2c,0xb8),(0x80519094,0x2c))
NEXT=0x8051982c
EDGES=((0x804f1e3c,0x80545100),(0x804f1e5c,0x80519094),
       (0x804f1e80,0x8051ad38),(0x804f1eb0,0x80004338),
       (0x804f1ec8,NEXT),(0x804f1ed0,0x8054514c))
def restore(old,bodies):
    if set(bodies)!=set(pc for pc,n in SPANS):raise ValueError("V103 exact wrapper body set differs")
    for pc,n in SPANS:
        if len(bodies[pc])!=n or be32(bodies[pc],n-4)!=BLR:
            raise ValueError("V103 original wrapper geometry differs")
    for pc,dst in EDGES:
        if target(be32(bodies[SPANS[0][0]],pc-SPANS[0][0]),pc,True)!=dst:
            raise ValueError("V103 original async wrapper call edge differs")
    out=bytearray(old)
    for i,(pc,n) in enumerate(SPANS):
        before=STUB+NOP*(n//4-2) if i==0 else NOP*(n//4)
        replace(out,pc,before,bodies[pc])
    replace(out,NEXT,NOP*2,STUB)
    reverse=bytearray(out);replace(reverse,NEXT,STUB,NOP*2)
    for i in reversed(range(len(SPANS))):
        pc,n=SPANS[i];before=STUB+NOP*(n//4-2) if i==0 else NOP*(n//4)
        replace(reverse,pc,bodies[pc],before)
    if bytes(reverse)!=old or out[:256]!=old[:256]:raise ValueError("V103 unrelated private mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing owner fixture overwrite")
    raw=a.owner.read_bytes();old=a.fixture.read_bytes()
    x=v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))
    x=v89(x,text_at(raw,OS_CALL,4),text_at(raw,V89_ROOT,V89_SIZE))
    x=v91(x,{pc:text_at(raw,pc,n) for pc,n in V91_SPANS})
    x=v93(x,text_at(raw,V93_ROOT,V93_SIZE))
    x=v94(x,text_at(raw,V94_ROOT,V94_SIZE))
    x=v95(x,{pc:text_at(raw,pc,n) for pc,n in V95_SPANS})
    x=v96(x,text_at(raw,V96_ROOT,V96_SIZE))
    x=v97(x,{pc:text_at(raw,pc,n) for pc,n in V97_SPANS})
    x=v99(x,text_at(raw,V99_ROOT,V99_SIZE))
    x=v100(x,{pc:text_at(raw,pc,n) for pc,n in V100_SPANS})
    x=v101(x,text_at(raw,V101_ROOT,V101_SIZE))
    x=v102(x,{pc:text_at(raw,pc,n) for pc,n in V102_SPANS})
    if x!=old:raise ValueError("V103 inherited authenticated V102 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,{pc:text_at(raw,pc,n) for pc,n in SPANS}))
    print("PASS: V103 original async SC wrapper and heap getter restored privately")
if __name__=="__main__":main()
