#!/usr/bin/env python3
"""V96 owner-local original directory query wrapper."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_ioctlv_v95 import (restore as v95,SPANS as V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
ROOT=0x804f0ad8
SIZE=0x98
CALL=0x804f0b58
DEST=0x8051a62c
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(old,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR or target(be32(body,CALL-ROOT),CALL,True)!=DEST:
        raise ValueError("V96 authenticated directory wrapper geometry differs")
    out=bytearray(old);replace(out,ROOT,EXPECTED,body)
    reverse=bytearray(out);replace(reverse,ROOT,body,EXPECTED)
    if bytes(reverse)!=old or out[:256]!=old[:256]:raise ValueError("V96 unrelated private mutation")
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
    if x!=old:raise ValueError("V96 inherited authenticated V95 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,text_at(raw,ROOT,SIZE)))
    print("PASS: V96 original directory query wrapper restored privately")
if __name__=="__main__":main()
