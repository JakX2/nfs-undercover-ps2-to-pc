#!/usr/bin/env python3
"""V104 private original IOS_OpenAsync request preparation."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_sc_async_entry_v103 import (restore as v103,SPANS as V103_SPANS,
    v102,V102_SPANS,v101,V101_ROOT,V101_SIZE,v100,V100_SPANS,
    v99,V99_ROOT,V99_SIZE,v97,V97_SPANS,v96,V96_ROOT,V96_SIZE,
    v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,v93,V93_ROOT,V93_SIZE,
    v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
ROOT=0x8051982c
SIZE=0x118
EDGES=((0x8051983c,0x80545104),(0x80519870,0x8051ad38),
       (0x80519900,0x805222c0),(0x80519920,0x805195ec),
       (0x80519930,0x80545150))
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(old,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR:
        raise ValueError("V104 original IOS_OpenAsync function geometry differs")
    for pc,dst in EDGES:
        if target(be32(body,pc-ROOT),pc,True)!=dst:
            raise ValueError("V104 authenticated IOS_OpenAsync edge differs")
    out=bytearray(old);replace(out,ROOT,EXPECTED,body)
    reverse=bytearray(out);replace(reverse,ROOT,body,EXPECTED)
    if bytes(reverse)!=old or out[:256]!=old[:256]:
        raise ValueError("V104 unrelated private code mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing owner file overwrite")
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
    x=v103(x,{pc:text_at(raw,pc,n) for pc,n in V103_SPANS})
    if x!=old:raise ValueError("V104 inherited authenticated V103 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,text_at(raw,ROOT,SIZE)))
    print("PASS: V104 IOS_OpenAsync original body restored privately")
if __name__=="__main__":main()
