#!/usr/bin/env python3
"""V99 owner-local exact original post-NAND sibling."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_es_close_v97 import (restore as v97,SPANS as V97_SPANS,
    v96,V96_ROOT,V96_SIZE,v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
ROOT=0x8052f94c
SIZE=0x114
NEXT=0x8051dff4
EDGES=((0x8052f9e0,0x8000443c),(0x8052f9f0,0x80004338),
       (0x8052fa00,0x80004338),(0x8052fa40,NEXT))
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(old,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR:raise ValueError("V99 original sibling geometry differs")
    for pc,dst in EDGES:
        if target(be32(body,pc-ROOT),pc,True)!=dst:raise ValueError("V99 direct edge differs")
    out=bytearray(old)
    replace(out,ROOT,EXPECTED,body)
    replace(out,NEXT,NOP*2,STUB)
    reverse=bytearray(out)
    replace(reverse,NEXT,STUB,NOP*2)
    replace(reverse,ROOT,body,EXPECTED)
    if bytes(reverse)!=old or old[:256]!=out[:256]:raise ValueError("V99 unrelated private mutation")
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
    x=v97(x,{pc:text_at(raw,pc,n) for pc,n in V97_SPANS})
    if x!=old:raise ValueError("V99 inherited authenticated V98 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,text_at(raw,ROOT,SIZE)))
    print("PASS: V99 original post-NAND sibling restored privately")
if __name__=="__main__":main()
