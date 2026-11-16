#!/usr/bin/env python3
"""Owner-private SHA-locked original EXIInit polling fixture; no proprietary opcodes in source."""
from pathlib import Path
import argparse,hashlib,struct
ORIGINAL_SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY=0x804EF9BC
STOP=0x804EFA14
SC=0x44000002
BLR=0x4E800020

def word(b,o):return struct.unpack_from('>I',b,o)[0]
def extract(source,address,n):
    for i in range(7):
        off,base,size=(word(source,k) for k in (i*4,0x48+i*4,0x90+i*4))
        if off>=0x100 and base<=address and address+n<=base+size and off+size<=len(source):
            return source[off+address-base:off+address-base+n]
    raise ValueError('owner original EXI range missing')

def make(owner):
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('owner DOL SHA-256 mismatch')
    prefix=extract(raw,ENTRY,STOP-ENTRY)
    if len(prefix)!=0x58 or word(prefix,0)!=0x9421ffe0:
        raise ValueError('original EXI entry/prologue mismatch')
    # Verify branch-to-loop sites and the final original address calculation.
    for pc in (0x804ef9e8,0x804ef9f8,0x804efa08):
        w=word(prefix,pc-ENTRY)
        if w>>26!=16:raise ValueError('missing original EXI loopback branch')
        disp=w&0xfffc
        if disp&0x8000:disp-=0x10000
        if (pc+disp)&0xffffffff!=0x804ef9dc:
            raise ValueError('changed original EXI loopback destination')
    if word(prefix,0x804efa10-ENTRY)>>26!=14:raise ValueError('missing original EXI argument calculation')
    body=prefix+struct.pack('>II',SC,BLR)
    out=bytearray(0x100+len(body))
    for off,v in ((0,0x100),(0x48,ENTRY),(0x90,len(body)),(0xe0,ENTRY)):
        struct.pack_into('>I',out,off,v)
    out[0x100:]=body
    return bytes(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('owner_dol',type=Path)
    parser.add_argument('out_dol',type=Path)
    args=parser.parse_args()
    if args.out_dol.exists():parser.error('refusing output overwrite')
    args.out_dol.write_bytes(make(args.owner_dol))
    print('PASS: V65 private EXI three-channel original-poll fixture created')
