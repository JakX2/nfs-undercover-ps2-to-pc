#!/usr/bin/env python3
"""Owner-private original PPC L2CR polls; original bytes extracted only at build time."""
import argparse
from pathlib import Path
from make_osinit_l2prefix_v61 import make as inherited, NEW_STOP as OLD_STOP
from make_osinit_cache_l1_v59 import OSINIT,NOP
from make_alarm_v47 import original_text,be32,SC,BLR,call_target

FINAL_STOP=0x80522644

def make(owner:Path)->bytes:
    dol=bytearray(inherited(owner))
    source=owner.read_bytes()
    original=original_text(source,OLD_STOP,FINAL_STOP-OLD_STOP)
    if len(original)!=0x58:
        raise ValueError('V62 expected original L2 poll through final debug-print branch')
    for site,dest in ((0x805225EC,0x804B7930),(0x805225F8,0x804B7930),
                      (0x80522600,0x804B7938),(0x80522610,0x804E50B8),
                      (0x80522614,0x804B7930),(0x80522624,0x804B7918),
                      (0x80522628,0x804B7930),(0x80522634,0x804B7938),
                      (0x80522640,0x804E50B8)):
        if call_target(original,site,OLD_STOP)!=dest:
            raise ValueError(f'V62 original cache call at {site:#x} changed')
    code_off=be32(dol,0);base=be32(dol,0x48);sz=be32(dol,0x90)
    if code_off<0x100 or base!=OSINIT or FINAL_STOP+8>base+sz or code_off+sz>len(dol):
        raise ValueError('V62 private DOL section changed')
    pos=code_off+OLD_STOP-base
    if (be32(dol,pos)!=SC or be32(dol,pos+4)!=BLR or
        any(be32(dol,pos+i)!=NOP for i in range(8,len(original),4))):
        raise ValueError('V62 refuses to replace non-synthetic L2 polling fixture')
    dol[pos:pos+len(original)]=original
    if be32(dol,code_off+FINAL_STOP-base)!=SC:
        raise ValueError('V62 enabled-L2 stop changed')
    return bytes(dol)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('original_owner_wii_dol',type=Path);p.add_argument('new_private_test_dol',type=Path)
    a=p.parse_args()
    if a.new_private_test_dol.exists():p.error('refuse overwrite original-code private image')
    a.new_private_test_dol.write_bytes(make(a.original_owner_wii_dol))
    print('PASS: V62 genuine original PowerPC L2 polling installed privately')
