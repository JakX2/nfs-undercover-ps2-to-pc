#!/usr/bin/env python3
"""Restore one authenticated original STM async request body in a private fixture."""
import argparse
import struct
from pathlib import Path

from make_alarm_v47 import call_target
from make_osinit_execparams_v28 import SC, BLR, NOP, text_at
from make_start_to_irq_enable_v68 import replace
from test_v77_continuous_ipc_ack_geometry import verify as verify_v77

IOCTL=0x8051a1a4
SIZE=0x138
EDGES=((0x8051a1b4,0x805450f4),(0x8051a1f8,0x8051ad38),
       (0x8051a298,0x805222c0),(0x8051a2a4,0x805222c0),
       (0x8051a2b8,0x805195ec),(0x8051a2c8,0x80545140))
EXPECTED=struct.pack(">II",SC,BLR)+struct.pack(">I",NOP)*(SIZE//4-2)

def validate_body(body):
    if len(body)!=SIZE:
        raise ValueError("V86 original async IOS span size differs")
    for pc,dst in EDGES:
        if call_target(body,IOCTL,pc)!=dst:
            raise ValueError("V86 original async IOS dependency differs")

def restore(fixture,body):
    validate_body(body)
    result=bytearray(fixture)
    replace(result,IOCTL,EXPECTED,body)
    if len(result)!=len(fixture) or result[:256]!=fixture[:256]:
        raise ValueError("V86 fixture header or size changed")
    if text_at(result,IOCTL,SIZE)!=body:
        raise ValueError("V86 fixture did not preserve original body")
    reverse=bytearray(result)
    replace(reverse,IOCTL,body,EXPECTED)
    if bytes(reverse)!=fixture:
        raise ValueError("V86 unrelated fixture difference")
    return bytes(result)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path)
    p.add_argument("owner",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("refusing to overwrite private fixture")
    data=a.fixture.read_bytes()
    verify_v77(data,a.owner)
    body=text_at(a.owner.read_bytes(),IOCTL,SIZE)
    result=restore(data,body)
    with a.output.open("xb") as out:
        out.write(result)
    print("PASS: V86 exact private original STM async IOS fixture")

if __name__=="__main__":
    main()
