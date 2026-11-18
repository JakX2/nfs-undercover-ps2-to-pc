#!/usr/bin/env python3
"""V93 owner-local next original resource service wrapper."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from make_start_to_ipc_ack_v77 import make as make_v77
from restore_stm_ioctl_v86 import restore as restore_v86,IOCTL,SIZE as IOCTL_SIZE
from restore_post_stm_v89 import restore as restore_v89,OS_CALL,ROOT as OLD_ROOT,SIZE as OLD_SIZE
from restore_resource_init_v91 import restore as restore_v91,SPANS
ROOT=0x804f05e8
SIZE=0x54
CALL=0x804f0610
DEST=0x80519944
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(fixture,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR or target(be32(body,CALL-ROOT),CALL,True)!=DEST:
        raise ValueError("V93 authenticated next service wrapper geometry differs")
    out=bytearray(fixture);replace(out,ROOT,EXPECTED,body)
    reverse=bytearray(out);replace(reverse,ROOT,body,EXPECTED)
    if bytes(reverse)!=fixture or out[:256]!=fixture[:256]:
        raise ValueError("V93 unrelated fixture mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    raw=a.owner.read_bytes();old=a.fixture.read_bytes()
    v86=restore_v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))
    v89=restore_v89(v86,text_at(raw,OS_CALL,4),text_at(raw,OLD_ROOT,OLD_SIZE))
    v91=restore_v91(v89,{pc:text_at(raw,pc,n) for pc,n in SPANS})
    if v91!=old:raise ValueError("V93 inherited authenticated V91 fixture differs")
    result=restore(old,text_at(raw,ROOT,SIZE))
    with a.output.open("xb") as f:f.write(result)
    print("PASS: V93 original next resource open wrapper restored privately")
if __name__=="__main__":main()
