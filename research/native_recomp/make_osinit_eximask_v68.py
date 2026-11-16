#!/usr/bin/env python3
"""Owner-private continuation of original OSInit -> EXIInit -> __OSMaskInterrupts.

Uses SHA-pinned owner original PowerPC data at unchanged guest addresses.
The only synthetic stop is after four EXI MMIO writes and before handler registration.
"""
from pathlib import Path
import argparse,struct
from make_osinit_exi_bridge_v66 import make as prev,EXI
from make_alarm_v47 import original_text,be32,SC,BLR,call_target
from make_osmask_v67 import MASK
EXI_MASK_CALL=0x804EFA14
STOP=0x804EFA34
MASK_BYTES=0x80
EXI_LENGTH=STOP-EXI+8

def make(owner:Path)->bytes:
    out=bytearray(prev(owner));raw=owner.read_bytes()
    # The existing large private section includes original SetInterruptMask but
    # contains only synthetic NOP fill at __OSMaskInterrupts. Replace strictly
    # the latter with owner-extracted original PowerPC instructions.
    off,base,length=(be32(out,j) for j in (4,0x4c,0x94))
    if base!=0x805265AC or not(off>=0x100 and off+length<=len(out) and base<=MASK and MASK+MASK_BYTES<=base+length):
        raise ValueError('unexpected original interrupt section geometry')
    at=off+MASK-base
    if any(be32(out,at+i)!=0x60000000 for i in range(0,MASK_BYTES,4)):
        raise ValueError('refuse replacement of non-synthetic mask section')
    orig_mask=original_text(raw,MASK,MASK_BYTES)
    if be32(orig_mask,0)>>26!=37 or be32(orig_mask,MASK_BYTES-4)!=BLR:
        raise ValueError('owner mask entry or epilogue changed')
    out[at:at+MASK_BYTES]=orig_mask
    # V66's EXI section is the final guest text section, with a synthetic
    # syscall at the first masked-interrupt call site. Extend it without
    # relocating the guest address or disturbing any preceding sections.
    off,base,length=(be32(out,j) for j in (0x18,0x60,0xa8))
    if base!=EXI or length!=0x60 or off+length!=len(out):
        raise ValueError('unexpected V66 EXI terminal image geometry')
    if be32(out,off+EXI_MASK_CALL-EXI)!=SC or be32(out,off+EXI_MASK_CALL-EXI+4)!=BLR:
        raise ValueError('EXI call site was not an explicit synthetic stop')
    orig_exi=original_text(raw,EXI,STOP-EXI)
    if orig_exi[:EXI_MASK_CALL-EXI]!=out[off:off+EXI_MASK_CALL-EXI]:
        raise ValueError('original EXI prefix differs from V66')
    call=original_text(raw,EXI_MASK_CALL,4)
    if call_target(call,EXI_MASK_CALL,EXI_MASK_CALL)!=MASK:
        raise ValueError('original EXI interrupt-mask target changed')
    for pc in (0x804EFA20,0x804EFA24,0x804EFA28,0x804EFA30):
        if be32(orig_exi,pc-EXI)>>26!=36:
            raise ValueError('original EXI MMIO store disappeared')
    out[off:]=orig_exi+struct.pack('>II',SC,BLR)
    struct.pack_into('>I',out,0xa8,EXI_LENGTH)
    return bytes(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('owner_dol',type=Path);p.add_argument('private_fixture',type=Path);a=p.parse_args()
    if a.private_fixture.exists():p.error('refusing output overwrite')
    a.private_fixture.write_bytes(make(a.owner_dol))
    print('PASS: V68 original EXI mask call and MMIO writes restored privately')
