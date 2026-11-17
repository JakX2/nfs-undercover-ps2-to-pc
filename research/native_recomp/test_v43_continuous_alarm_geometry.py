#!/usr/bin/env python3
"""V43 owner-original alarm PPC, bounded test-stop and no-overwrite verifier."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_syscall_v42 import make as make_v42
from make_start_to_epilogue_v41 import sections_of
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_alarm_v43 import OSINIT,OLD_STOP,STOP,ALARM,SET,SHUTDOWN,START

def verify(image:bytes,owner:Path)->None:
    prior=make_v42(owner) # includes SHA, source/fixture code guards, V42
    if len(image)<256 or word(image,0xe0)!=START:
        raise ValueError("V43 original Wii DOL header malformed")
    allowed_header=set(range(7*4))|set(range(0x90,0x90+7*4))
    allowed_header.update(range(0x1c,0x1c+2*4))
    for i in range(256):
        if i not in allowed_header and image[i]!=prior[i]:
            raise ValueError("V43 modified unexpected owner-original DOL metadata")
    before,olddata=sections_of(prior)
    after,newdata=sections_of(image)
    if olddata!=newdata:raise ValueError("V43 modified original startup relocation/oracle data")
    if [g for g,_ in before]!=[g for g,_ in after]:
        raise ValueError("V43 altered original Wii guest section bases")
    ranges=((OLD_STOP,STOP+8),(SET,SET+0x24),(ALARM,ALARM+0x58),
            (SHUTDOWN,SHUTDOWN+0x88))
    for (base,old),(guest,new) in zip(before,after):
        if base!=guest or len(new)<len(old):
            raise ValueError("V43 original guest section truncated/rebased")
        for i,value in enumerate(old):
            pc=base+i
            if not any(a<=pc<b for a,b in ranges) and new[i]!=value:
                raise ValueError("V43 modified previously verified native PPC")
        if len(new)>len(old):
            if base!=OSINIT:raise ValueError("V43 expanded an unrelated Wii text section")
            for i in range(len(old),len(new)):
                pc=base+i
                if ALARM<=pc<ALARM+0x58:continue
                if new[i]!=struct.pack(">I",NOP)[i%4]:
                    raise ValueError("V43 inserted code outside alarm function span")
    def read(pc:int,size:int)->bytes:
        found=[bytes(blob[pc-base:pc-base+size]) for base,blob in after
               if base<=pc and pc+size<=base+len(blob)]
        if len(found)!=1:raise ValueError("V43 original alarm PPC has ambiguous mapping")
        return found[0]
    for pc,length in ((OLD_STOP,4),(SET,0x24),(ALARM,0x58),(SHUTDOWN,0x88)):
        if read(pc,length)!=text_at(owner.read_bytes(),pc,length):
            raise ValueError("V43 original alarm/helper code differs from owner")
    if read(STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V43 next original OSInit service lacks test-only guard")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V43 alarm-call, shutdown helpers and no-overwrite guards")
