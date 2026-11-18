#!/usr/bin/env python3
"""V102 owner-local original SC pathname preparation and bounded strlen."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_sc_loading_v101 import (restore as v101,ROOT as V101_ROOT,SIZE as V101_SIZE,
    v100,V100_SPANS,v99,V99_ROOT,V99_SIZE,v97,V97_SPANS,
    v96,V96_ROOT,V96_SIZE,v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
ROOT=0x8051e71c
STRLEN=0x80544ac0
NEXT=0x8051e3dc
SPANS=((ROOT,0xc8),(STRLEN,0x1c))
EDGES=((0x8051e73c,STRLEN),(0x8051e750,0x8054b4b4),
       (0x8051e788,NEXT),(0x8051e798,0x8054b4b4),(0x8051e7a0,STRLEN))
def restore(old,bodies):
    if set(bodies)!=set(a for a,n in SPANS):raise ValueError("V102 original body set differs")
    for a,n in SPANS:
        if len(bodies[a])!=n or be32(bodies[a],n-4)!=BLR:raise ValueError("V102 original body terminal differs")
    for pc,dst in EDGES:
        if target(be32(bodies[ROOT],pc-ROOT),pc,True)!=dst:
            raise ValueError("V102 original SC path direct edge differs")
    out=bytearray(old)
    for i,(a,n) in enumerate(SPANS):
        before=STUB+NOP*(n//4-2) if i==0 else NOP*(n//4)
        replace(out,a,before,bodies[a])
    replace(out,NEXT,NOP*2,STUB)
    reverse=bytearray(out)
    replace(reverse,NEXT,STUB,NOP*2)
    for i in reversed(range(len(SPANS))):
        a,n=SPANS[i];before=STUB+NOP*(n//4-2) if i==0 else NOP*(n//4)
        replace(reverse,a,bodies[a],before)
    if bytes(reverse)!=old or out[:256]!=old[:256]:raise ValueError("V102 unrelated private mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private fixture overwrite")
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
    if x!=old:raise ValueError("V102 inherited V101 original fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,{a:text_at(raw,a,n) for a,n in SPANS}))
    print("PASS: V102 original pathname and strlen bodies restored privately")
if __name__=="__main__":main()
