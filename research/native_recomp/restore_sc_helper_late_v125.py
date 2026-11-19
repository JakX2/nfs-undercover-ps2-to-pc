#!/usr/bin/env python3
"""V125: late restoration of the SHA-authenticated SC helper, after V104.

Do not modify the V77 root fixture: V89+ extensions compare the inherited
fixture against that exact original-free baseline. The late restoration
touches only the original SC helper's pre-existing SC/BLR+NOP placeholder.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from extend_private_text import STUB,NOP,install,unpack
from make_osinit_execparams_v28 import ORIGINAL_SHA, BLR, text_at

ENTRY=0x8051E5BC
NEXT_KNOWN=0x8051E71C
MAX_SPAN=NEXT_KNOWN-ENTRY
MIN_SPAN=8

def prefix_kind(inherited:bytes,owner:bytes)->int:
    """0=unmapped, 1=SC/BLR stub, 2=NOP pair, 3=authenticated, 4=other."""
    slots=unpack(inherited)
    found=[(base,blob) for kind,index,base,blob in slots
           if kind==0 and base<=ENTRY and ENTRY+8<=base+len(blob)]
    if len(found)!=1:
        return 0
    base,blob=found[0]
    prefix=bytes(blob[ENTRY-base:ENTRY-base+8])
    if prefix==STUB:
        return 1
    if prefix==NOP*2:
        return 2
    if prefix==text_at(owner,ENTRY,8):
        return 3
    return 4

def placeholder_capacity(inherited:bytes)->int:
    slots=unpack(inherited)
    found=[(base,blob) for kind,index,base,blob in slots
           if kind==0 and base<=ENTRY and ENTRY+8<=base+len(blob)]
    if len(found)!=1:
        raise ValueError("V125 helper entry not uniquely mapped")
    base,blob=found[0]
    offset=ENTRY-base
    if bytes(blob[offset:offset+8])!=STUB:
        raise ValueError("V125 helper entry not synthetic stub")
    cap=min(MAX_SPAN,len(blob)-offset)
    n=8
    while n+4<=cap and bytes(blob[offset+n:offset+n+4])==NOP:
        n+=4
    return n

def select_body(owner:bytes,max_len:int=MAX_SPAN)->bytes:
    if not (MIN_SPAN<=max_len<=MAX_SPAN) or max_len%4:
        raise ValueError("V125 helper available span invalid")
    code=text_at(owner,ENTRY,max_len)
    terminal=struct.pack(">I",BLR)
    ends=[n+4 for n in range(4,len(code),4)
          if code[n:n+4]==terminal]
    if not ends:
        raise ValueError("V125 original helper has no bounded return")
    size=max(ends)
    if size<MIN_SPAN or size>MAX_SPAN or size%4:
        raise ValueError("V125 original helper size outside bounded neighbor")
    body=code[:size]
    if body[:8] in (STUB,NOP*2) or body[-4:]!=terminal:
        raise ValueError("V125 original helper code not authenticated")
    return body

def restore(old:bytes,body:bytes)->bytes:
    if len(body)<MIN_SPAN or len(body)>MAX_SPAN or len(body)%4 or body[-4:]!=struct.pack(">I",BLR):
        raise ValueError("V125 helper body shape differs")
    prior=unpack(old)
    located=[(base,data) for kind,index,base,data in prior
             if kind==0 and base<=ENTRY and ENTRY+len(body)<=base+len(data)]
    if len(located)!=1:
        raise ValueError("V125 helper range not covered by inherited text")
    expected=STUB+NOP*((len(body)-8)//4)
    result=install(old,[(ENTRY,expected,body)])
    if result[:256]!=old[:256] or len(result)!=len(old):
        raise ValueError("V125 inherited DOL header or layout modified")
    before=unpack(old)
    after=unpack(result)
    if len(before)!=len(after):
        raise ValueError("V125 private DOL section set changed")
    for left,right in zip(before,after):
        if left[:3]!=right[:3] or len(left[3])!=len(right[3]):
            raise ValueError("V125 private section metadata changed")
        kind,index,base,code=left
        recovered=bytearray(right[3])
        if kind==0 and base<=ENTRY and ENTRY+len(body)<=base+len(code):
            offset=ENTRY-base
            recovered[offset:offset+len(body)]=expected
        if recovered!=code:
            raise ValueError("V125 unrelated original bytes changed")
    return result

def make(fixture:Path,owner:Path)->bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V125 owner SHA-256 validation failed")
    inherited=fixture.read_bytes()
    return restore(inherited,select_body(raw,placeholder_capacity(inherited)))

FAILURE_CODES=(
    "V125 original helper has no bounded return",
    "V125 original helper size outside bounded neighbor",
    "V125 original helper code not authenticated",
    "V125 helper body shape differs",
    "V125 helper range not covered by inherited text",
    "V125 inherited DOL header or layout modified",
    "V125 private DOL section set changed",
    "V125 private section metadata changed",
    "V125 unrelated original bytes changed",
    "private text patch does not match exact prior placeholder",
    "V125 owner SHA-256 validation failed",
    "V125 helper entry not uniquely mapped",
    "V125 helper entry not synthetic stub",
    "V125 helper available span invalid",
)
def failure_code(exc:Exception)->int:
    try:
        return FAILURE_CODES.index(str(exc))+1
    except ValueError:
        return 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("inherited_private_fixture",type=Path)
    p.add_argument("authenticated_owner",type=Path)
    p.add_argument("output_private_fixture",type=Path)
    args=p.parse_args()
    if args.output_private_fixture.exists() or args.output_private_fixture.is_symlink():
        p.error("refusing to overwrite private fixture")
    try:
        result=make(args.inherited_private_fixture,args.authenticated_owner)
        with args.output_private_fixture.open("xb") as out:
            out.write(result)
    except Exception as exc:
        # Only a fixed numeric category is published, never raw private text.
        try:
            kind=prefix_kind(args.inherited_private_fixture.read_bytes(),
                             args.authenticated_owner.read_bytes())
        except Exception:
            kind=0
        print(f"V125_LATE_PREFIX kind={kind}")
        print(f"V125_LATE_DETAIL code={failure_code(exc):02d}")
        print("V125_LATE_RESTORE ok=0")
        raise SystemExit(1)
    print("V125_LATE_RESTORE ok=1")

if __name__=="__main__":
    main()
