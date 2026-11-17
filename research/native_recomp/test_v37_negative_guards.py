#!/usr/bin/env python3
"""Private V37 owner-original negative guards: only independently authored tests.

Rejects mutated guest instructions, helper bodies, stops and DOL geometry
without publishing or logging any private Wii data.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct

from make_start_to_vectorclear_v37 import STOP,word
from make_start_to_mark_v36 import MARK
from test_v37_continuous_vectorclear_geometry import verify


def guest_offset(image:bytes,pc:int)->int:
    for index in range(7):
        off,guest,size=(word(image,k+4*index) for k in (0,0x48,0x90))
        if guest<=pc and pc+4<=guest+size and off+size<=len(image):
            return off+pc-guest
    raise ValueError("private mutation guest coordinate unmapped")


def requires_rejection(fixture:bytes,original:bytes,at:int)->None:
    changed=bytearray(fixture)
    changed[at] ^= 1
    try:
        verify(bytes(changed),original)
    except ValueError:
        return
    raise AssertionError("mutated original Wii native fixture wrongly accepted")


def run(fixture:bytes,original:bytes)->int:
    verify(fixture,original)
    checks=0
    sites=(
        0x80520bf4,0x80520c44,0x80520cc4,0x80520cc8,0x80520cdc,
        0x80520cf0,0x80520cf4,0x80520d08,0x80520d20,0x80520d64,
        0x80520d7c,STOP,MARK,MARK+20,0x80520f28,0x805208ac
    )
    for site in sites:
        requires_rejection(fixture,original,guest_offset(fixture,site))
        checks+=1
    for at in (0xe0,0x48+4,0x90+4,0xac,0x64):
        requires_rejection(fixture,original,at)
        checks+=1
    bad_original=bytearray(original)
    bad_original[-1]^=1
    try:
        verify(fixture,bytes(bad_original))
    except ValueError:
        checks+=1
    else:
        raise AssertionError("owner-original SHA mutation was accepted")
    return checks


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_test_dol",type=Path)
    p.add_argument("private_original_dol",type=Path)
    a=p.parse_args()
    checks=run(a.private_test_dol.read_bytes(),a.private_original_dol.read_bytes())
    print(f"PASS: original Wii V37 private source/stop/memory corruption guards={checks}")
