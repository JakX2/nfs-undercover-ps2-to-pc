#!/usr/bin/env python3
"""Verify V125 changes only the authenticated SC helper NOP span, preserving V77."""
import argparse
import struct
from pathlib import Path
from make_start_to_ipc_ack_v77 import make as previous
from make_start_to_sc_helper_v125 import ENTRY,NOP_WORD,extent,authenticated_span
from make_start_to_epilogue_v41 import sections_of
from make_start_to_si_sampling_v58 import data_sections

def verify(actual:bytes,owner:Path)->None:
    earlier=previous(owner)
    old_text,_=sections_of(earlier)
    new_text,_=sections_of(actual)
    if len(actual)!=len(earlier) or actual[:256]!=earlier[:256]:
        raise ValueError("V125 fixture header/layout modified")
    if data_sections(actual)!=data_sections(earlier):
        raise ValueError("V125 inherited data sections modified")
    if [(p,len(s)) for p,s in old_text]!=[(p,len(s)) for p,s in new_text]:
        raise ValueError("V125 translated text section geometry modified")
    length=extent(earlier)
    body=authenticated_span(owner,length)
    hits=[(i,base) for i,(base,blob) in enumerate(old_text)
          if base<=ENTRY and ENTRY+length<=base+len(blob)]
    if len(hits)!=1:
        raise ValueError("V125 private helper does not map uniquely")
    index,base=hits[0]
    expected=list(old_text)
    copy=bytearray(expected[index][1])
    offset=ENTRY-base
    if copy[offset:offset+length]!=NOP_WORD*(length//4):
        raise ValueError("V125 helper fixture overlaps inherited code")
    copy[offset:offset+length]=body
    expected[index]=(base,copy)
    if new_text!=expected:
        raise ValueError("V125 fixture differs outside authenticated helper span")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("original_owner",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.original_owner)
    print("PASS: V125 authenticated private helper geometry")
