#!/usr/bin/env python3
"""V95 private authenticated original synchronous IOS vector preparation."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_title_query_v94 import restore as v94,ROOT as V94_ROOT,SIZE as V94_SIZE
from restore_next_resource_v93 import restore as v93,ROOT as V93_ROOT,SIZE as V93_SIZE
from make_start_to_ipc_ack_v77 import make as make_v77
from restore_stm_ioctl_v86 import restore as v86,IOCTL,SIZE as IOCTL_SIZE
from restore_post_stm_v89 import restore as v89,OS_CALL,ROOT as V89_ROOT,SIZE as V89_SIZE
from restore_resource_init_v91 import restore as v91,SPANS as V91_SPANS
SPANS=((0x8051a62c,0xdc),(0x8051a40c,0x13c))
EDGES=((0x8051a63c,0x80545100),(0x8051a674,0x8051ad38),(0x8051a6cc,0x8051a40c),
       (0x8051a6e4,0x805195ec),(0x8051a6f4,0x8054514c),(0x8051a41c,0x80545100),
       (0x8051a470,0x805222c0),(0x8051a4c8,0x805222c0),(0x8051a510,0x805222c0),(0x8051a534,0x8054514c))
NEXT=0x804f0ad8
def restore(old,bodies):
    if set(bodies)!=set(pc for pc,n in SPANS):raise ValueError("V95 exact body set differs")
    for pc,n in SPANS:
        if len(bodies[pc])!=n or be32(bodies[pc],n-4)!=BLR:raise ValueError("V95 function geometry differs")
    for pc,dst in EDGES:
        base=next(a for a,n in SPANS if a<=pc<a+n)
        if target(be32(bodies[base],pc-base),pc,True)!=dst:raise ValueError("V95 direct edge differs")
    out=bytearray(old)
    for pc,n in SPANS:
        before=(STUB+NOP*(n//4-2)) if pc==SPANS[0][0] else NOP*(n//4)
        replace(out,pc,before,bodies[pc])
    reverse=bytearray(out)
    for pc,n in SPANS:
        before=(STUB+NOP*(n//4-2)) if pc==SPANS[0][0] else NOP*(n//4)
        replace(reverse,pc,bodies[pc],before)
    if bytes(reverse)!=old or old[:256]!=out[:256]:raise ValueError("V95 unrelated private mutation")
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
    if x!=old:raise ValueError("V95 inherited authenticated V94 fixture differs")
    with a.output.open("xb") as f:f.write(restore(old,{pc:text_at(raw,pc,n) for pc,n in SPANS}))
    print("PASS: V95 original synchronous IOS vector bodies restored privately")
if __name__=="__main__":main()
