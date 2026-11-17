#!/usr/bin/env python3
"""V56 continuous original EXIGetID channel 0/device 2 immediate transactions.

The ordinary zero-cache path executes original lock/select/imm/sync/deselect
and inline unlock instructions. Unsupported alternate paths fail explicitly.
Owner SHA verification is inherited from V55; no PPC body is stored here.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_idcache_v55 import make as previous,ID,EPILOGUE,EPILOGUE_END,STOP as OLD_STOP,START
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_start_to_vectorcopy_v38 import word

STOP=0x804EFAB4
SLOW=0x804EFDD4
IRQMASK=0x804EE894
IMM=0x804EE984
SYNC=0x804EED9C
PROBE=0x804EF09C
SELECT=0x804EF3EC
DESELECT=0x804EF51C
LOCK=0x804EFB80
HWREV=0x80521008
GETIRQ=0x8052660C
UNMASK=0x805269BC
# Explicitly forbidden alternate branches: console type discrimination,
# queued external callbacks, and physical card detection (next milestone).
CONSOLE_CALL=0x804EEF64
QUEUE_CALL=0x804F0018
RANGES=((IRQMASK,0x804EE984),(IMM,0x804EEC00),(SYNC,0x804EF018),
        (SELECT,0x804EF51C),(DESELECT,0x804EF61C),(LOCK,0x804EFC7C),
        (HWREV,0x80521018),(GETIRQ,0x8052661C),(UNMASK,0x80526A3C))
EDGES=((0x804EFF00,LOCK),(0x804EFF1C,SELECT),(0x804EFF48,IMM),
       (0x804EFF5C,SYNC),(0x804EFF80,IMM),(0x804EFF94,SYNC),
       (0x804EFFA8,DESELECT),(0x804EFFE8,IRQMASK),
       (0x804EFC54,IRQMASK),(0x804EEF58,HWREV),
       (CONSOLE_CALL,0x8051FD44),(QUEUE_CALL,0x80548798))

def verify_original(raw:bytes):
    for lo,hi in RANGES:
        code=text_at(raw,lo,hi-lo)
        if len(code)!=hi-lo or word(code,len(code)-4)!=BLR:
            raise ValueError("original EXI helper body/return missing")
    for site,dest in EDGES:
        if call_target(text_at(raw,site,4),site,site)!=dest:
            raise ValueError("original EXI transaction call graph changed")
    if word(text_at(raw,OLD_STOP,4),0)>>26!=32:
        raise ValueError("original post-ID EXIInit load changed")

def make(owner:Path)->bytes:
    old=previous(owner)
    raw=owner.read_bytes()
    verify_original(raw)
    text,data=sections_of(old)
    if len(text)!=7 or len(data)!=2:
        raise ValueError("inherited Wii DOL topology changed")

    def install(pc,expected,new):
        hits=[(i,base,code) for i,(base,code) in enumerate(text)
              if base<=pc and pc+len(expected)<=base+len(code)]
        if len(hits)!=1 or len(expected)!=len(new):
            raise ValueError("V56 original guest range outside unique inherited mapping")
        i,base,code=hits[0]
        off=pc-base
        if code[off:off+len(expected)]!=expected:
            raise ValueError("V56 refused overwrite of previously verified code")
        code[off:off+len(expected)]=new
        text[i]=(base,code)

    def nop_region(lo,hi):
        return struct.pack(">I",NOP)*((hi-lo)//4)

    for lo,hi in RANGES:
        original=bytearray(text_at(raw,lo,hi-lo))
        if lo<=CONSOLE_CALL<hi:
            at=CONSOLE_CALL-lo
            original[at:at+4]=struct.pack(">I",SC)
        install(lo,nop_region(lo,hi),original)
    install(PROBE,nop_region(PROBE,PROBE+8),struct.pack(">II",SC,BLR))
    body=bytearray(text_at(raw,SLOW,EPILOGUE-SLOW))
    body[QUEUE_CALL-SLOW:QUEUE_CALL-SLOW+4]=struct.pack(">I",SC)
    install(SLOW,struct.pack(">II",SC,BLR)+nop_region(SLOW+8,EPILOGUE),body)
    install(OLD_STOP,struct.pack(">III",SC,BLR,NOP),
            text_at(raw,OLD_STOP,4)+struct.pack(">II",SC,BLR))
    out=bytearray(old[:256])
    for i,(base,blob) in enumerate(text):
        off=len(out)
        for field,val in ((0,off),(0x48,base),(0x90,len(blob))):
            struct.pack_into(">I",out,field+4*i,val)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    for i,(base,blob) in enumerate(data):
        off=len(out)
        for field,val in ((0x1c,off),(0x64,base),(0xac,len(blob))):
            struct.pack_into(">I",out,field+4*i,val)
        out.extend(blob)
        out.extend(b"\0"*((-len(out))%4))
    if out[:256]!=old[:256] or word(out,0xe0)!=START:
        raise ValueError("V56 altered original guest DOL entry or segment metadata")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original",type=Path)
    p.add_argument("private_output",type=Path)
    a=p.parse_args()
    if a.private_output.exists() or a.private_output.is_symlink():
        p.error("refusing to overwrite private DOL")
    a.private_output.write_bytes(make(a.owner_original))
    print("PASS: V56 owner-original uncached EXI transaction fixture")
