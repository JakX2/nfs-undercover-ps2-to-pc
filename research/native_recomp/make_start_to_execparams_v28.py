#!/usr/bin/env python3
"""Private recovered V28 continuous Wii __start through original __OSGetExecParams.

Reuses verified V27 and owner SHA-pinned DOL; copies original instructions
only at runtime into ephemeral test segments. C0 is an explicit synthetic
syscall stop. It does not implement complete Wii OS initialization.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_interrupt_v27 import make as make_v27
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR

EXEC_CALL = 0x805206BC
STOP = 0x805206C0
EXEC = 0x80523B1C


def section_offset(image: bytes, index: int, pc: int, size: int) -> int:
    off, base, length=(struct.unpack_from(">I",image,field+index*4)[0]
                       for field in (0,0x48,0x90))
    if (off<256 or base>pc or pc+size>base+length or
            off+length>len(image) or off+pc-base+size>len(image)):
        raise ValueError("recovered PowerPC section geometry mismatch")
    return off+pc-base


def make(owner: Path) -> bytes:
    source=owner.read_bytes()
    if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original Wii DOL SHA mismatch")
    result=bytearray(make_v27(owner))
    at=section_offset(result,1,EXEC_CALL,12)
    if result[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("expected prior V27 execparams callsite test stop")
    original_call=get_text(source,EXEC_CALL,4)
    if linked_target(struct.unpack_from(">I",original_call)[0],EXEC_CALL)!=EXEC:
        raise ValueError("original __OSGetExecParams call target changed")
    # Execute the genuine call and retain the authentic return PC at C0.
    result[at:at+4]=original_call
    result[at+4:at+12]=struct.pack(">II",SC,BLR)
    target=section_offset(result,5,EXEC,36)
    result[target:target+36]=get_text(source,EXEC,36)
    return bytes(result)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        p.error("refusing private output overwrite")
    args.output.write_bytes(make(args.owner_dol))
    print("PASS: original Wii V28 continuous execparams private fixture generated")


if __name__=="__main__":
    main()
