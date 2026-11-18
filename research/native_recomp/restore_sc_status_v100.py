#!/usr/bin/env python3
"""V100 owner-only authentic system configuration status path."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_post_nand_v99 import (restore as v99,ROOT as V99_ROOT,SIZE as V99_SIZE,
    v97,V97_SPANS,v96,V96_ROOT,V96_SIZE,v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
SPANS=((0x8051dff4,0x78),(0x8051e5a4,0x14))
NEXT=0x8051dd50
EDGES=((0x8051e004,0x80545104),(0x8051e01c,0x8051e5a4),
       (0x8051e04c,NEXT),(0x8051e050,0x8051e5bc),
       (0x8051e058,0x80545150))
def restore(old,bodies):
    if set(bodies)!=set(a for a,n in SPANS):raise ValueError("V100 body set differs")
    for addr,size in SPANS:
        if len(bodies[addr])!=size or be32(bodies[addr],size-4)!=BLR:
            raise ValueError("V100 authenticated body terminal differs")
    for pc,dst in EDGES:
        if target(be32(bodies[SPANS[0][0]],pc-SPANS[0][0]),pc,True)!=dst:
            raise ValueError("V100 authenticated status edge differs")
    out=bytearray(old)
    for i,(addr,size) in enumerate(SPANS):
        prior=STUB+NOP*(size//4-2) if i==0 else NOP*(size//4)
        replace(out,addr,prior,bodies[addr])
    replace(out,NEXT,NOP*2,STUB)
    rev=bytearray(out)
    replace(rev,NEXT,STUB,NOP*2)
    for i,(addr,size) in reversed(tuple(enumerate(SPANS))):
        prior=STUB+NOP*(size//4-2) if i==0 else NOP*(size//4)
        replace(rev,addr,bodies[addr],prior)
    if bytes(rev)!=old or out[:256]!=old[:256]:raise ValueError("V100 unrelated private mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path)
    p.add_argument("owner",type=Path)
    p.add_argument("output",type=Path)
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
    if x!=old:raise ValueError("V100 inherited original fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,{a:text_at(raw,a,n) for a,n in SPANS}))
    print("PASS: V100 original SC status body and getter restored privately")
if __name__=="__main__":main()
