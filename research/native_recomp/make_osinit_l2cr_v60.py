#!/usr/bin/env python3
"""Private original Wii L2CR read/branch fixture; no original PPC bytes in source."""
import argparse
import struct
from pathlib import Path
from make_osinit_cache_l1_v59 import make as inherited, CACHE, CACHE_STOP, OSINIT, NOP
from make_alarm_v47 import original_text, call_target, be32, SC, BLR

MFL2CR=0x804B7930
MTL2CR=0x804B7938
L2_DISABLED_STOP=0x805225A0
L2_ENABLED_STOP=0x80522644


def make(owner: Path) -> bytes:
    previous = bytearray(inherited(owner))
    original = owner.read_bytes()
    body=original_text(original,CACHE_STOP,12)  # read L2CR; test bit31; branch
    helper=original_text(original,MFL2CR,16)
    if (len(body)!=12 or len(helper)!=16 or
        call_target(body,CACHE_STOP,CACHE_STOP)!=MFL2CR or
        be32(helper,4)!=BLR or be32(helper,12)!=BLR or
        be32(helper,0)!=0x7c79faa6 or be32(helper,8)!=0x7c79fba6 or
        be32(body,8)!=0x408200a8):
        raise ValueError('V60 original L2CR call or branch changed')
    section_off,base,section_len=[be32(previous,x) for x in (0,0x48,0x90)]
    helper_off,helper_base,helper_len=[be32(previous,x) for x in (0x10,0x58,0xa0)]
    if not(section_off>=256 and base==OSINIT and
        CACHE_STOP+12<=base+section_len and L2_ENABLED_STOP+8<=base+section_len and
        helper_base<=MFL2CR and MFL2CR+16<=helper_base+helper_len and
        helper_off>=256 and helper_off+helper_len<=len(previous)):
        raise ValueError('V60 synthetic DOL section geometry changed')
    insert=section_off+CACHE_STOP-base
    if [be32(previous,insert+4*i) for i in range(3)]!=[SC,BLR,NOP]:
        raise ValueError('V60 inherited terminal was not V59 SC/BLR/NOP')
    previous[insert:insert+12]=body
    for stop in (L2_DISABLED_STOP,L2_ENABLED_STOP):
        index=section_off+stop-base
        if any(be32(previous,index+4*j)!=NOP for j in range(2)):
            raise ValueError('V60 refuses to replace nonsynthetic branch target')
        struct.pack_into('>II',previous,index,SC,BLR)
    offset=helper_off+MFL2CR-helper_base
    if any(be32(previous,offset+4*j)!=NOP for j in range(4)):
        raise ValueError('V60 refuses to replace nonsynthetic L2CR helper')
    previous[offset:offset+16]=helper
    return bytes(previous)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_owner_wii_dol',type=Path)
    ap.add_argument('new_private_dol',type=Path)
    args=ap.parse_args()
    if args.new_private_dol.exists():ap.error('V60 refuses to overwrite private DOL')
    args.new_private_dol.write_bytes(make(args.original_owner_wii_dol))
    print('PASS: V60 original Wii L2CR read and bit31 branch fixture created privately')
