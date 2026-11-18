#!/usr/bin/env python3
"""V91 private authenticated subsystem, resource initializer and native leaf."""
import argparse,struct
from pathlib import Path
from make_osinit_execparams_v28 import SC,BLR,NOP,text_at,be32,target
from make_start_to_ipc_ack_v77 import make as make_v77
from restore_stm_ioctl_v86 import restore as restore_v86,IOCTL,SIZE as IOCTL_SIZE
from restore_post_stm_v89 import restore as restore_v89,OS_CALL,ROOT as OLD_ROOT,SIZE as OLD_SIZE
from extend_private_text import install,NOP as PAD,STUB

ROOT=0x8051e7e4
CHILD=0x804f0cdc
LEAF=0x8054b4b4
SPANS=((ROOT,0x12c),(CHILD,0x128),(LEAF,0xc0))
EDGES=((0x8051e800,0x805265ac),(0x8051e810,0x805265d4),(0x8051e824,0x805265d4),
       (0x8051e838,0x805265d4),(0x8051e83c,CHILD),(0x8051e84c,0x804f05e8),
       (0x8051e860,0x804f0b70),(0x8051e880,0x804f0ad8),(0x8051e89c,LEAF),
       (0x8051e8a0,0x804f063c),(0x8051e8b4,0x80522f00),(0x8051e8bc,0x80527b4c),
       (0x8051e8c0,0x805265ac),(0x8051e8cc,0x805265d4),(0x8051e8d4,0x80521018),
       (0x8051e8e0,0x805265ac),(0x8051e8ec,0x805265d4),(0x8051e8f4,0x8051e5bc),
       (0x804f0d00,0x80519084),(0x804f0d08,0x8051907c),(0x804f0d48,0x80522f00),
       (0x804f0d58,LEAF),(0x804f0d64,0x80519944),(0x804f0da8,0x80522f00),
       (0x804f0dc0,0x8051908c),(0x804f0dd4,0x8051aa04))
BOUNDARIES=(0x804f05e8,0x804f063c,0x804f0ad8,0x804f0b70,0x8051e5bc)

def restore(fixture,bodies):
    if set(bodies)!=set(pc for pc,_ in SPANS):
        raise ValueError("V91 bounded original body set differs")
    for pc,size in SPANS:
        if len(bodies[pc])!=size or be32(bodies[pc],size-4)!=BLR:
            raise ValueError("V91 original function geometry differs")
    for pc,dest in EDGES:
        base=next(b for b,n in SPANS if b<=pc<b+n)
        if target(be32(bodies[base],pc-base),pc,True)!=dest:
            raise ValueError("V91 original direct dependency differs")
    patches=[(pc,(STUB+PAD*(size//4-2)) if pc==ROOT else PAD*(size//4),bodies[pc])
             for pc,size in SPANS]
    patches.extend((pc,PAD*2,STUB) for pc in BOUNDARIES)
    result=install(fixture,patches)
    for pc,body in bodies.items():
        if text_at(result,pc,len(body))!=body:raise ValueError("V91 private body restoration differs")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    raw=a.owner.read_bytes();old=a.fixture.read_bytes()
    verified=restore_v86(make_v77(a.owner),text_at(raw,IOCTL,IOCTL_SIZE))
    if restore_v89(verified,text_at(raw,OS_CALL,4),text_at(raw,OLD_ROOT,OLD_SIZE))!=old:
        raise ValueError("V91 prior fixture does not match authenticated V89 geometry")
    result=restore(old,{pc:text_at(raw,pc,n) for pc,n in SPANS})
    with a.output.open("xb") as out:out.write(result)
    print("PASS: V91 original resource initializer and native leaf restored privately")
if __name__=="__main__":
    main()
