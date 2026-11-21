#!/usr/bin/env python3
"""V248 restore two authentic Wii callback bodies into a PRIVATE fixture.

V247 owner CI proved the reduced AOT fixture contains exactly 96 NOP
words at _isfsFuncCb and 30 NOP words at nandOpenCallback. Restore only
these fixed ranges from the SHA-256-authenticated owner DOL. Reject
all unexpected non-NOP source bytes and any altered ISFS/IPC controls.
The output stays in an owner-only temporary directory; never publish
original instruction bytes or translated game source.
"""
import argparse
import hashlib
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_start_to_irq_enable_v68 import replace
from audit_v245_generated_callback import SPANS
from extend_private_text import NOP

TARGETS=("cb","nand")
CONTROLS=("isfs","ipc")
BLR=b"\x4e\x80\x00\x20"

def restore(original:bytes,fixture:bytes,expected_sha:str=ORIGINAL_SHA)->bytes:
    if hashlib.sha256(original).hexdigest()!=expected_sha:
        raise ValueError("V248 authenticated owner digest differs")
    bodies={}
    for key in CONTROLS:
        address,size=SPANS[key]
        if text_at(fixture,address,size)!=text_at(original,address,size):
            raise ValueError("V248 unchanged original control function differs")
    for key in TARGETS:
        address,size=SPANS[key]
        before=text_at(fixture,address,size)
        body=text_at(original,address,size)
        if before!=NOP*(size//4) or len(body)!=size or (
                body[:4]==NOP or body[-4:]!=BLR):
            raise ValueError("V248 callback placeholder or original body invalid")
        bodies[key]=(address,before,body)
    candidate=bytearray(fixture)
    for key in TARGETS:
        address,before,body=bodies[key]
        replace(candidate,address,before,body)
    for key in TARGETS+CONTROLS:
        address,size=SPANS[key]
        if text_at(candidate,address,size)!=text_at(original,address,size):
            raise ValueError("V248 candidate callback restoration mismatch")
    # Reverse *exactly* the two restored spans. Every other byte,
    # DOL section header, data section, and BSS metadata must be intact.
    reverse=bytearray(candidate)
    for key in reversed(TARGETS):
        address,before,body=bodies[key]
        replace(reverse,address,body,before)
    if bytes(reverse)!=fixture:
        raise ValueError("V248 unrelated private fixture changed")
    return bytes(candidate)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("authenticated_original",type=Path)
    p.add_argument("original_free_fixture",type=Path)
    p.add_argument("private_candidate_output",type=Path)
    a=p.parse_args()
    if a.private_candidate_output.exists() or a.private_candidate_output.is_symlink():
        print("V248_RESTORE result=failed")
        return 1
    try:
        original=a.authenticated_original.read_bytes()
        old=a.original_free_fixture.read_bytes()
        candidate=restore(original,old)
        with a.private_candidate_output.open("xb") as f:
            f.write(candidate)
    except (OSError,ValueError):
        print("V248_RESTORE result=failed")
        return 1
    print("V248_RESTORE owner=1 cb=1 nand=1 controls=1 reversible=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
