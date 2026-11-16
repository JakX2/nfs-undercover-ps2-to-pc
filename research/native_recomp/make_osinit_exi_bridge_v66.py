#!/usr/bin/env python3
"""Private owner-original direct OSInit -> EXI polling bridge, no embedded original opcodes."""
from pathlib import Path
import argparse,struct
from make_osinit_cache_return_v64 import make as inherited
from make_alarm_v47 import original_text,call_target,be32,SC,BLR
from make_exi_poll_v65 import ENTRY as EXI, STOP as EXI_STOP
OSINIT=0x80520670
CALL=0x805208C4
DOL_ENTRY_BASE=0x100

def make(owner:Path)->bytes:
    out=bytearray(inherited(owner))
    raw=owner.read_bytes()
    call=original_text(raw,CALL,4)
    if call_target(call,CALL,CALL)!=EXI:
        raise ValueError('owner-original OSInit EXI branch changed')
    first,base,size=(be32(out,k) for k in (0,0x48,0x90))
    if base!=OSINIT or first<0x100 or first+size>len(out):
        raise ValueError('unexpected V64 OSInit private DOL geometry')
    at=first+CALL-base
    if be32(out,at)!=SC or be32(out,at+4)!=BLR:
        raise ValueError('refuse overwrite of non-synthetic OSInit terminal')
    out[at:at+4]=call
    prefix=original_text(raw,EXI,EXI_STOP-EXI)
    if len(prefix)!=0x58 or be32(prefix,0)!=0x9421ffe0:
        raise ValueError('original EXI entry/prefix differs')
    for pc in (0x804ef9e8,0x804ef9f8,0x804efa08):
        op=be32(prefix,pc-EXI)
        if op>>26!=16:
            raise ValueError('missing original EXI channel-loop conditional backedge')
        offset=op&0xfffc
        if offset&0x8000: offset-=0x10000
        if pc+offset!=0x804ef9dc:
            raise ValueError('original EXI loopback destination changed')
    # Seven source-backed guest text slots, with a new owner-private slot at index 6.
    if any(be32(out,k)!=0 for k in (0x18,0x60,0xa8)):
        raise ValueError('V64 expected seventh text slot empty')
    block=prefix+struct.pack('>II',SC,BLR)
    start=len(out)
    for p,v in ((0x18,start),(0x60,EXI),(0xa8,len(block))):
        struct.pack_into('>I',out,p,v)
    out.extend(block)
    return bytes(out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('owner_original_dol',type=Path);p.add_argument('private_output_dol',type=Path)
    a=p.parse_args()
    if a.private_output_dol.exists():p.error('refusing output overwrite')
    a.private_output_dol.write_bytes(make(a.owner_original_dol))
    print('PASS: V66 restored original OSInit EXI branch and added owner-private EXI polling prefix')
