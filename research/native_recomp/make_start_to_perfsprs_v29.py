#!/usr/bin/env python3
"""V29 private continuous __start performance SPR initialization fixture.

Extends verified owner-original V28 to six authentic MMCR/PMC helper calls.
All PowerPC bodies are extracted from a SHA-pinned private Wii DOL.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_execparams_v28 import make as make_v28, section_offset
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR, NOP

OSINIT = 0x80520670
PREV_STOP = 0x805206C0
NEW_STOP = 0x805206F0
PERF = 0x804B7964
PERF_REGS = (952, 956, 953, 954, 957, 958)


def spr_num(word: int) -> int:
    return (((word >> 11) & 31) << 5) | ((word >> 16) & 31)


def make(owner: Path) -> bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("owner Wii DOL SHA-256 mismatch")
    result=bytearray(make_v28(owner))
    os_at=section_offset(result,1,PREV_STOP,NEW_STOP-PREV_STOP+8)
    if result[os_at:os_at+8] != struct.pack(">II",SC,BLR):
        raise ValueError("V28 original ExecParams return boundary missing")
    chunk=get_text(raw,PREV_STOP,NEW_STOP-PREV_STOP)
    if len(chunk)!=48:
        raise ValueError("original performance initialization length changed")
    for i in range(6):
        callpc=PREV_STOP+i*8+4
        branch=struct.unpack_from(">I",chunk,i*8+4)[0]
        if linked_target(branch,callpc) != PERF+i*8:
            raise ValueError("original performance helper call graph changed")
        # On the authentic path, each helper is preceded by integer load-immediate.
        li=struct.unpack_from(">I",chunk,i*8)[0]
        if li >> 26 != 14:
            raise ValueError("original performance helper input initialization changed")
    result[os_at:os_at+48]=chunk
    result[os_at+48:os_at+56]=struct.pack(">II",SC,BLR)
    for i,spr in enumerate(PERF_REGS):
        pc=PERF+i*8
        off=section_offset(result,2,pc,8)
        if result[off:off+8] != struct.pack(">II",NOP,NOP):
            raise ValueError("unexpected prior PowerPC helper bytes in fixture")
        body=get_text(raw,pc,8)
        op,ret=struct.unpack(">II",body)
        if (op>>26!=31 or ((op>>1)&1023)!=467 or
                ((op>>21)&31)!=3 or spr_num(op)!=spr or ret!=BLR):
            raise ValueError("original MMCR/PMC helper instruction signature changed")
        result[off:off+8]=body
    return bytes(result)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        p.error("refusing private output overwrite")
    args.output.write_bytes(make(args.owner_dol))
    print("PASS: V29 original performance SPR fixture generated privately")


if __name__=="__main__":
    main()
