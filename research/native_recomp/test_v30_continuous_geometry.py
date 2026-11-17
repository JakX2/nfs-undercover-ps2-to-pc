#!/usr/bin/env python3
"""Private original-code geometry checks for V30 continuous HID4/FP startup."""
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_hid4_v30 import (
    OSINIT,PREVIOUS,STOP,REPORT,HELPERS,HID0_READ,HID0_WRITE,
    SPEC,NONIEEE,HID4,HID_END,be32,spr_number
)
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text,linked_target
from make_start_to_data_v23 import SC,BLR

def mapped(image:bytes,index:int,guest:int,size:int)->bytes:
    off,base,n=(be32(image,k+index*4) for k in (0,0x48,0x90))
    if off<256 or base>guest or guest+size>base+n or off+n>len(image):
        raise ValueError("private original code outside mapped DOL bounds")
    return image[off+guest-base:off+guest-base+size]

def check(image:bytes,original:bytes)->None:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("wrong original DOL SHA-256")
    if len(image)<256 or be32(image,0xe0)!=0x8000403C:
        raise ValueError("not a continuous original __start image")
    if mapped(image,1,PREVIOUS,16)!=get_text(original,PREVIOUS,16):
        raise ValueError("original HID4/speculation/nonIEEE callsites changed")
    if mapped(image,1,STOP,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("V30 test-only stop missing")
    if mapped(image,5,REPORT,8)!=struct.pack(">II",SC,BLR):
        raise ValueError("guarded OSReport stop missing")
    for guest,n in ((HID0_READ,8),(HID0_WRITE,8),(SPEC,40),
                    (NONIEEE,8),(HID4,80)):
        if mapped(image,2,guest,n)!=get_text(original,guest,n):
            raise ValueError("original source-backed HID4 routine differs")
    # Owner original PPC function boundary/call topology verification.
    continuation=mapped(image,1,PREVIOUS,16)
    for at,dest in ((0x805206F4,HID4),(0x805206F8,SPEC),(0x805206FC,NONIEEE)):
        if linked_target(be32(continuation,at-PREVIOUS),at)!=dest:
            raise ValueError("original OSInit nested call no longer targets helper")
    code=mapped(image,2,HID4,80)
    if linked_target(be32(code,0x30),HID4+0x30)!=REPORT:
        raise ValueError("HID4 error-report branch not guarded")
    # Check all seven test code sections for guest overlap.
    ranges=[]
    for i in range(7):
        off,addr,length=(be32(image,k+4*i) for k in (0,0x48,0x90))
        if off<256 or length<4 or off+length>len(image) or addr&3:
            raise ValueError("invalid original Wii DOL header section")
        for a,b in ranges:
            if not(addr>=b or addr+length<=a):
                raise ValueError("overlapping Wii code regions")
        ranges.append((addr,addr+length))

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_dol",type=Path)
    parser.add_argument("owner_original",type=Path)
    args=parser.parse_args()
    check(args.private_dol.read_bytes(),args.owner_original.read_bytes())
    print("PASS: continuous original Wii V30 HID4/speculation/FP/test-boundary geometry")

if __name__=="__main__":
    main()
