#!/usr/bin/env python3
"""V38 original-Wii private vector memcpy mutation/geometry negative checks."""
from __future__ import annotations
import argparse
from pathlib import Path

from make_start_to_vectorcopy_v38 import (
    COPY_CALL,COPY_START,STOP,TEMPLATE_SRC,PRIVATE_DATA_GUEST,word
)
from test_v38_continuous_vectorcopy_geometry import verify


def byte_offset(image:bytes,guest:int)->int:
    for i in range(7):
        off,base,n=(word(image,k+i*4) for k in (0,0x48,0x90))
        if base<=guest<base+n and off+n<=len(image):
            return off+guest-base
    for i in range(2):
        off,base,n=(word(image,k+i*4) for k in (0x1c,0x64,0xac))
        if base<=guest<base+n and off+n<=len(image):
            return off+guest-base
    raise ValueError("test mutation guest address not mapped")


def test(image:bytes,original:bytes)->int:
    verify(image,original)
    count=0
    sites=(
      0x80520bf4,0x80520c44,0x80520cc4,0x80520cdc,
      0x80520cf0,0x80520d08,0x80520d20,0x80520d64,
      0x80520d7c,COPY_START,COPY_CALL,COPY_CALL+4,
      STOP,0x80520f28,0x80520ec0,0x80520ec4,
      0x80520f58,0x80520f5c,0x804e50a0,
      PRIVATE_DATA_GUEST,PRIVATE_DATA_GUEST+0x57,
      PRIVATE_DATA_GUEST+0x58,PRIVATE_DATA_GUEST+0x97
    )
    for site in sites:
        mutate=bytearray(image)
        mutate[byte_offset(image,site)]^=1
        try:verify(bytes(mutate),original)
        except ValueError: count+=1
        else:raise AssertionError("altered Wii original input accepted")
    for at in (0xe0,0x20,0x68,0xb0,0x1c,0x64,0xac):
        mutate=bytearray(image)
        mutate[at]^=1
        try:verify(bytes(mutate),original)
        except ValueError:count+=1
        else:raise AssertionError("mutated private DOL header accepted")
    mutate=bytearray(original)
    mutate[-1]^=1
    try:verify(image,bytes(mutate))
    except ValueError:count+=1
    else:raise AssertionError("unverified owner original SHA mutation accepted")
    return count


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_test_dol",type=Path)
    p.add_argument("owner_dol",type=Path)
    args=p.parse_args()
    checks=test(args.private_test_dol.read_bytes(),args.owner_dol.read_bytes())
    print(f"PASS: original Wii V38 private vector-copy mutation guards={checks}")
