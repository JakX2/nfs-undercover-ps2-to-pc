#!/usr/bin/env python3
"""Independently verify exact V57 restored guest ranges and private data slot."""
import argparse,struct
from pathlib import Path
from make_start_to_exi_transaction_v56 import make as previous,STOP as PREV_STOP,PROBE
from make_start_to_exi_return_v57 import RANGES,GUARDS,VERSION_POINTER,version_data
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word

def verify(actual:bytes,owner:Path):
    old=previous(owner);raw=owner.read_bytes()
    header=bytearray(old[:256])
    for h,v in ((0x1c,len(old)),(0x64,VERSION_POINTER),(0xac,4)):
        struct.pack_into(">I",header,h+8,v)
    if actual[:256]!=header or len(actual)!=len(old)+4 or actual[-4:]!=version_data(raw):
        raise ValueError("V57 private data pointer or executable geometry changed")
    text,data=sections_of(old)
    new,newdata=sections_of(actual)
    if data!=newdata:raise ValueError("V57 inherited data changed")
    expected=bytearray(old)
    expected[:256]=header
    for lo,hi in RANGES:
        matches=[(i,base,code) for i,(base,code) in enumerate(text) if base<=lo and hi<=base+len(code)]
        if len(matches)!=1:raise ValueError("V57 range mapping missing")
        i,base,code=matches[0]
        for pc in range(lo,hi,4):
            inherited=SC if pc in (PREV_STOP,PROBE) else BLR if pc in (PREV_STOP+4,PROBE+4) else NOP
            if word(code,pc-base)!=inherited:
                raise ValueError("V57 inherited original instructions overwritten")
            at=word(old,i*4)+pc-base
            expected[at:at+4]=struct.pack(">I",SC) if pc in GUARDS else text_at(raw,pc,4)
    expected.extend(version_data(raw))
    if expected!=actual:raise ValueError("V57 original/non-original byte mismatch")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path)
    a=p.parse_args();verify(a.fixture.read_bytes(),a.owner)
    print("PASS: exact V57 EXI probe/return restoration and private version pointer")
