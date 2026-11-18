#!/usr/bin/env python3
"""V94 owner-local exact title-query wrapper and explicit IOS_Ioctlv boundary."""
import argparse
from pathlib import Path
from make_osinit_execparams_v28 import BLR,text_at,be32,target
from make_start_to_irq_enable_v68 import replace
from extend_private_text import NOP,STUB
from restore_next_resource_v93 import restore as restore_v93,ROOT as OLD_ROOT,SIZE as OLD_SIZE
from make_start_to_ipc_ack_v77 import make as make_v77
from restore_stm_ioctl_v86 import restore as restore_v86,IOCTL,SIZE as IOCTL_SIZE
from restore_post_stm_v89 import restore as restore_v89,OS_CALL,ROOT as V89_ROOT,SIZE as V89_SIZE
from restore_resource_init_v91 import restore as restore_v91,SPANS
ROOT=0x804f0b70
SIZE=0x98
CALL=0x804f0bd4
DEST=0x8051a62c
EXPECTED=STUB+NOP*(SIZE//4-2)
def restore(fixture,body):
    if len(body)!=SIZE or be32(body,SIZE-4)!=BLR or target(be32(body,CALL-ROOT),CALL,True)!=DEST:
        raise ValueError("V94 authenticated title query wrapper geometry differs")
    out=bytearray(fixture)
    replace(out,ROOT,EXPECTED,body)
    replace(out,DEST,NOP*2,STUB)
    reverse=bytearray(out)
    replace(reverse,DEST,STUB,NOP*2)
    replace(reverse,ROOT,body,EXPECTED)
    if bytes(reverse)!=fixture or out[:256]!=fixture[:256]:
        raise ValueError("V94 unrelated fixture mutation")
    return bytes(out)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    raw=a.owner.read_bytes();old=a.fixture.read_bytes()
    v86=restore_v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))
    v89=restore_v89(v86,text_at(raw,OS_CALL,4),text_at(raw,V89_ROOT,V89_SIZE))
    v91=restore_v91(v89,{pc:text_at(raw,pc,n) for pc,n in SPANS})
    v93=restore_v93(v91,text_at(raw,OLD_ROOT,OLD_SIZE))
    if v93!=old:raise ValueError("V94 inherited authenticated V93 fixture differs")
    result=restore(old,text_at(raw,ROOT,SIZE))
    with a.output.open("xb") as f:f.write(result)
    print("PASS: V94 original title query wrapper and explicit IOS_Ioctlv guard restored privately")
if __name__=="__main__":main()
