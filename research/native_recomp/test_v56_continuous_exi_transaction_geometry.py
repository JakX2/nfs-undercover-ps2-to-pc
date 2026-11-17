#!/usr/bin/env python3
"""Exact old/new private byte-range oracle for V56; no game data in source."""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_idcache_v55 import make as before,STOP as PREVIOUS_STOP
from make_start_to_exi_transaction_v56 import RANGES,PROBE,SLOW,EPILOGUE,STOP,CONSOLE_CALL,QUEUE_CALL
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(image:bytes,owner:Path):
    previous=before(owner)
    original=owner.read_bytes()
    if len(image)!=len(previous) or image[:256]!=previous[:256]:
        raise ValueError("V56 changed original DOL section geometry")
    old,olddata=sections_of(previous)
    new,newdata=sections_of(image)
    if olddata!=newdata:
        raise ValueError("V56 modified inherited data payloads")
    replacements={}
    for lo,hi in (*RANGES,(SLOW,EPILOGUE)):
        for pc in range(lo,hi,4):
            expected=struct.pack(">I",SC) if pc in (CONSOLE_CALL,QUEUE_CALL) else text_at(original,pc,4)
            if pc in replacements:raise ValueError("V56 overlapping allowed ranges")
            replacements[pc]=expected
    replacements[PROBE]=struct.pack(">I",SC)
    replacements[PROBE+4]=struct.pack(">I",BLR)
    replacements[PREVIOUS_STOP]=text_at(original,PREVIOUS_STOP,4)
    replacements[STOP]=struct.pack(">I",SC)
    replacements[STOP+4]=struct.pack(">I",BLR)
    observed=set()
    for (base,prior),(newbase,current) in zip(old,new):
        if base!=newbase or len(prior)!=len(current):
            raise ValueError("V56 guest text mapping shifted")
        for i in range(0,len(prior),4):
            pc=base+i
            if pc in replacements:
                if pc in observed:raise ValueError("V56 repeated guest address")
                observed.add(pc)
                if current[i:i+4]!=replacements[pc]:
                    raise ValueError("V56 owner instruction/test guard mismatch")
                prior_expected=(SC if pc in (SLOW,PREVIOUS_STOP) else
                                BLR if pc in (SLOW+4,STOP) else NOP)
                if prior[i:i+4]!=struct.pack(">I",prior_expected):
                    raise ValueError("V56 replaced non-synthetic inherited instruction")
            elif prior[i:i+4]!=current[i:i+4]:
                raise ValueError("V56 altered previous original Wii code outside declared spans")
    if observed!=set(replacements):
        raise ValueError("V56 replacement coverage incomplete")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path)
    p.add_argument("owner",type=Path)
    a=p.parse_args()
    verify(a.fixture.read_bytes(),a.owner)
    print("PASS: V56 all changed words match original EXI ranges or explicit guards")
