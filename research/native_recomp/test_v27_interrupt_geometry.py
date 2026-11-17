#!/usr/bin/env python3
"""Source-only geometry verifier for private original V27 interrupt call seam."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from make_start_to_interrupt_v27 import PREVIOUS_STOP, NEXT_STOP
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_start_to_time_v26_recovered import START
from make_start_to_data_v23 import SC, BLR
import hashlib


def verify(image: bytes, original: bytes) -> None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong owner image hash")
    if len(image)<256 or struct.unpack_from(">I",image,0xe0)[0]!=START:
        raise ValueError("wrong original continuous __start entry")
    idx=1
    off, guest, length = (struct.unpack_from(">I",image,k+4*idx)[0]
                          for k in (0,0x48,0x90))
    if off<256 or not(guest<=PREVIOUS_STOP and NEXT_STOP+8<=guest+length):
        raise ValueError("invalid OSInit native section bounds")
    at=off+PREVIOUS_STOP-guest
    if image[at:at+8]!=get_text(original,PREVIOUS_STOP,8):
        raise ValueError("original post-V26 OSInit BL/fallthrough code not present")
    if image[at+8:at+16]!=struct.pack(">II",SC,BLR):
        raise ValueError("V27 explicit pre-execparams test-only stop missing")

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_dol",type=Path)
    p.add_argument("owner_original",type=Path)
    args=p.parse_args()
    verify(args.private_dol.read_bytes(),args.owner_original.read_bytes())
    print("PASS: exact original V27 post-time interrupt-call and execparams boundary geometry")


if __name__=="__main__":
    main()
