#!/usr/bin/env python3
"""V125 owner-only canonical V86-V104 fixture reconstruction plus late SC helper.

All game instruction bytes are read from the SHA-authenticated original Wii DOL.
Each inherited restoration validates its exact expected placeholder and graph.
This file contains no game-derived executable instructions.
"""
import argparse
import hashlib
from pathlib import Path

from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from restore_sc_async_submit_v104 import (
    restore as v104,ROOT,SIZE,
    v103,V103_SPANS,v102,V102_SPANS,v101,V101_ROOT,V101_SIZE,
    v100,V100_SPANS,v99,V99_ROOT,V99_SIZE,
    v97,V97_SPANS,v96,V96_ROOT,V96_SIZE,
    v95,V95_SPANS,v94,V94_ROOT,V94_SIZE,
    v93,V93_ROOT,V93_SIZE,
    v91,V91_SPANS,v89,V89_ROOT,V89_SIZE,OS_CALL,v86,IOCTL,IOCTL_SIZE,make_v77,
)
from restore_sc_helper_late_v125 import restore as restore_helper,placeholder_capacity,select_body

def make(owner:Path)->bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V125 original-owner authentication differs")
    fixture=v86(make_v77(owner),text_at(raw,IOCTL,IOCTL_SIZE))
    fixture=v89(fixture,text_at(raw,OS_CALL,4),text_at(raw,V89_ROOT,V89_SIZE))
    fixture=v91(fixture,{pc:text_at(raw,pc,n) for pc,n in V91_SPANS})
    fixture=v93(fixture,text_at(raw,V93_ROOT,V93_SIZE))
    fixture=v94(fixture,text_at(raw,V94_ROOT,V94_SIZE))
    fixture=v95(fixture,{pc:text_at(raw,pc,n) for pc,n in V95_SPANS})
    fixture=v96(fixture,text_at(raw,V96_ROOT,V96_SIZE))
    fixture=v97(fixture,{pc:text_at(raw,pc,n) for pc,n in V97_SPANS})
    fixture=v99(fixture,text_at(raw,V99_ROOT,V99_SIZE))
    fixture=v100(fixture,{pc:text_at(raw,pc,n) for pc,n in V100_SPANS})
    fixture=v101(fixture,text_at(raw,V101_ROOT,V101_SIZE))
    fixture=v102(fixture,{pc:text_at(raw,pc,n) for pc,n in V102_SPANS})
    fixture=v103(fixture,{pc:text_at(raw,pc,n) for pc,n in V103_SPANS})
    fixture=v104(fixture,text_at(raw,ROOT,SIZE))
    if text_at(fixture,OS_CALL,4)!=text_at(raw,OS_CALL,4):
        raise ValueError("V125 canonical OS branch not authenticated")
    body=select_body(raw,placeholder_capacity(fixture))
    result=restore_helper(fixture,body)
    if text_at(result,OS_CALL,4)!=text_at(raw,OS_CALL,4):
        raise ValueError("V125 canonical OS branch changed during helper restoration")
    return result

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("authenticated_owner",type=Path)
    p.add_argument("output_private_fixture",type=Path)
    a=p.parse_args()
    if a.output_private_fixture.exists() or a.output_private_fixture.is_symlink():
        p.error("refusing private fixture overwrite")
    try:
        result=make(a.authenticated_owner)
        with a.output_private_fixture.open("xb") as out:
            out.write(result)
    except Exception:
        print("V125_CANONICAL result=failed")
        return 1
    print("V125_CANONICAL result=verified")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
