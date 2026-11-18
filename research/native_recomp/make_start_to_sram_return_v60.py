#!/usr/bin/env python3
"""Private original SRAM initializer, read-only DMA and no-change configuration."""
import argparse,struct
from pathlib import Path
from make_start_to_si_return_v59 import make as previous, STOP as PREV_STOP, START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word
STOP=0x805208D0
SRAM=0x80528754
RANGES=((SRAM,0x80528954),(0x80528954,0x80528974),(0x80528BFC,0x80528C34),
        (0x80522294,0x805222C0),(0x804EECA4,0x804EED9C),(0x804EFC7C,0x804EFD54))
GUARDS=(0x80528974,0x804EFD10)
EDGES=((PREV_STOP,SRAM),(0x80528784,0x80522294),(0x80528794,0x804EFB80),
       (0x805287B4,0x804EF3EC),(0x805287F0,0x804EE984),(0x80528800,0x804EED9C),
       (0x80528824,0x804EECA4),(0x80528838,0x804EED9C),(0x8052884C,0x804EF51C),
       (0x80528860,0x804EFC7C),(0x805288B8,0x80528954),(0x80528924,0x80528954),
       (0x804EFD10,0x80548798))
def make(owner):
    old=previous(owner);raw=owner.read_bytes()
    for pc,dest in EDGES:
        if call_target(text_at(raw,pc,4),pc,pc)!=dest:raise ValueError("V60 original SRAM call edge changed")
    text,_=sections_of(old)
    for lo,hi in RANGES:
        hits=[(base,code) for base,code in text if base<=lo and hi<=base+len(code)]
        if len(hits)!=1:raise ValueError("V60 SRAM original range not uniquely mapped")
        b,c=hits[0];at=lo-b
        if c[at:at+hi-lo]!=struct.pack(">I",NOP)*((hi-lo)//4):
            raise ValueError("V60 attempted to overwrite prior original code")
        body=bytearray(text_at(raw,lo,hi-lo))
        if lo<=GUARDS[1]<hi:body[GUARDS[1]-lo:GUARDS[1]-lo+4]=struct.pack(">I",SC)
        c[at:at+hi-lo]=body
    b,c=text[5];at=GUARDS[0]-b
    if c[at:at+8]!=struct.pack(">II",NOP,NOP):raise ValueError("V60 SRAM write guard overlaps original")
    c[at:at+8]=struct.pack(">II",SC,BLR)
    b,c=text[1];at=PREV_STOP-b
    if c[at:at+12]!=struct.pack(">III",SC,BLR,NOP):raise ValueError("V59 prior OSInit stop changed")
    c[at:at+12]=text_at(raw,PREV_STOP,4)+struct.pack(">II",SC,BLR)
    out=bytearray(old)
    for i,(base,body) in enumerate(text):
        off=word(old,4*i)
        if len(body)!=word(old,0x90+4*i):raise ValueError("V60 original text geometry changed")
        out[off:off+len(body)]=body
    if out[:256]!=old[:256] or word(out,0xe0)!=START:raise ValueError("V60 changed DOL entry")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("owner",type=Path)
    p.add_argument("private_output",type=Path);a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():p.error("refusing private overwrite")
    a.private_output.write_bytes(make(a.owner))
    print("PASS: V60 private original SRAM read-only fixture")
