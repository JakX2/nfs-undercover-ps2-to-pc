#!/usr/bin/env python3
"""Private original SIInit cold return: one immediate type transfer, three queued.

Only owner-original code supplies PPC bytes. Delayed alarm scheduling and
interrupt completion remain explicit test-only failing guards.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_si_sampling_v58 import make as previous, STOP as PREV_STOP, REPEAT_STOP, OS_STOP as STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

SI_END=0x80532140
TYPE=0x80532AA8
TYPE_END=0x80532C5C
TRANSFER=0x8053268C
TRANSFER_END=0x805327F8
START_TRANSFER=0x80532140
START_TRANSFER_END=0x805322F0
DELAY_CALL=0x80532778
CALLBACK=0x805327F8
ALARM_CALLBACK=0x80532600
RANGES=((PREV_STOP,SI_END),(START_TRANSFER,START_TRANSFER_END),
        (TRANSFER,TRANSFER_END),(TYPE,TYPE_END))
GUARDS=(CALLBACK,ALARM_CALLBACK)
EDGES=((0x8053210c,TYPE),(0x80532114,TYPE),(0x8053211c,TYPE),(0x80532124,TYPE),
       (0x80532aec,0x8052a844),(0x80532be0,0x8052a844),
       (0x80532c34,TRANSFER),(0x80532708,0x8052a844),
       (0x80532798,START_TRANSFER),(DELAY_CALL,0x80521384),
       (0x8053269c,0x805450ec),(0x805327e4,0x80545138),
       (0x80532150,0x80545100),(0x805322dc,0x8054514c),
       (0x80532ab8,0x80545104),(0x80532c48,0x80545150))

def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:
            raise ValueError("original SI discovery call graph changed")
    for lo,hi in RANGES:
        if word(text_at(raw,hi-4,4),0)!=BLR:
            raise ValueError("original SI transfer or init lacks return")
    text,_=sections_of(old)
    base,body=text[5]
    if base!=0x80522540 or not base<=PREV_STOP<TYPE_END<=base+len(body):
        raise ValueError("original SI discovery ranges outside inherited section")
    for lo,hi in RANGES:
        at=lo-base
        expected=bytearray(struct.pack(">I",NOP)*((hi-lo)//4))
        if lo==PREV_STOP:
            for pc in (PREV_STOP,REPEAT_STOP):
                expected[pc-lo:pc-lo+8]=struct.pack(">II",SC,BLR)
        if body[at:at+len(expected)]!=expected:
            raise ValueError("V59 refused to overwrite original code")
        replacement=bytearray(text_at(raw,lo,hi-lo))
        if lo<=DELAY_CALL<hi:
            replacement[DELAY_CALL-lo:DELAY_CALL-lo+4]=struct.pack(">I",SC)
        body[at:at+len(expected)]=replacement
    for pc in GUARDS:
        at=pc-base
        if body[at:at+8]!=struct.pack(">II",NOP,NOP):
            raise ValueError("V59 callback guard overlaps original code")
        body[at:at+8]=struct.pack(">II",SC,BLR)
    out=bytearray(old)
    off=word(old,5*4)
    if word(old,0x90+5*4)!=len(body):
        raise ValueError("V59 changed original text geometry")
    out[off:off+len(body)]=body
    if out[:256]!=old[:256] or word(out,0xe0)!=START:
        raise ValueError("V59 changed original entry or DOL header")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner",type=Path);p.add_argument("private_output",type=Path)
    a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing original overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: private V59 original SI type discovery and queue fixture")
