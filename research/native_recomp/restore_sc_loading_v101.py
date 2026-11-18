#!/usr/bin/env python3
"""V101 original Wii SC configuration loading body to selected early helper."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_sc_status_v100 import (restore as v100,SPANS as V100_SPANS,
    v99,V99_ROOT,V99_SIZE,v97,V97_SPANS,v96,V96_ROOT,V96_SIZE,
    v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,v93,V93_ROOT,V93_SIZE,
    v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77)
ROOT=0x8051dd50
SIZE=0x114
TARGETS=(0x8051e71c,0x8051e518)
EDGES=((0x8051dd60,0x80545104),(0x8051ddc4,TARGETS[0]),
       (0x8051ddd4,TARGETS[1]),(0x8051de38,0x804f1e2c),
       (0x8051de48,0x804f1d64),(0x8051de50,0x80545150))
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(old,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR:raise ValueError("V101 original SC child geometry differs")
    for site,dest in EDGES:
        if target(be32(body,site-ROOT),site,True)!=dest:raise ValueError("V101 original SC child edge differs")
    out=bytearray(old)
    replace(out,ROOT,EXPECTED,body)
    for addr in TARGETS:replace(out,addr,NOP*2,STUB)
    rev=bytearray(out)
    for addr in reversed(TARGETS):replace(rev,addr,STUB,NOP*2)
    replace(rev,ROOT,body,EXPECTED)
    if bytes(rev)!=old or out[:256]!=old[:256]:raise ValueError("V101 unrelated private mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
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
    x=v99(x,text_at(raw,V99_ROOT,V99_SIZE))
    x=v100(x,{pc:text_at(raw,pc,n) for pc,n in V100_SPANS})
    if x!=old:raise ValueError("V101 inherited authenticated V100 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,text_at(raw,ROOT,SIZE)))
    print("PASS: V101 original SC configuration loading body privately restored")
if __name__=="__main__":main()
