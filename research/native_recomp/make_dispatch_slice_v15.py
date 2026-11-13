#!/usr/bin/env python3
"""Build a private test-only DOL of two PPC functions and synthetic stop syscall.

The owner-derived output DOL contains proprietary game instructions and MUST
NOT be committed, redistributed, or included in source-only test archives.
"""
import argparse
import hashlib
import struct
from pathlib import Path

OWNER_SHA256='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
STOP_PC=0x80004200

def read_original_text(path:Path,addr:int,size:int)->bytes:
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=OWNER_SHA256:
        raise ValueError('owner DOL SHA-256 differs; refusing unverified build')
    for i in range(7):
        offset,base,length=(struct.unpack_from('>I',data,4*i)[0],
                            struct.unpack_from('>I',data,0x48+4*i)[0],
                            struct.unpack_from('>I',data,0x90+4*i)[0])
        if base<=addr and addr+size<=base+length and length:
            start=offset+addr-base
            chunk=data[start:start+size]
            if len(chunk)!=size:
                raise ValueError('owner DOL code section shorter than declared')
            return chunk
    raise ValueError('owner PPC function slice not inside initialized text')

def make_slice(original:Path|None):
    if original is None:
        text_addr=0x80004000
        entry=0x80004000
        instructions=(0x7c0802a6,0x90010008,0x48000011,0x80010008,
                      0x7c0803a6,0x4e800020,0x38630001,0x4e800020)
        text=b''.join(struct.pack('>I',x) for x in instructions)
    else:
        text_addr=0x8007adac
        entry=0x8007adc8
        text=read_original_text(original,text_addr,140)
    off1=0x100
    off2=(off1+len(text)+3)&~3
    b=bytearray(off2+8)
    # Two executable text sections: selected PPC function span, then the
    # wholly synthetic test-only sc;blr terminator at STOP_PC.
    for off,val in ((0x00,off1),(0x04,off2),(0x48,text_addr),
                    (0x4c,STOP_PC),(0x90,len(text)),(0x94,8),
                    (0xe0,entry)):
        struct.pack_into('>I',b,off,val)
    b[off1:off1+len(text)]=text
    struct.pack_into('>II',b,off2,0x44000002,0x4e800020)
    return bytes(b),entry

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--owner-dol',type=Path)
    a=parser.parse_args()
    if a.output.exists():
        raise SystemExit('refusing to overwrite existing slice')
    payload,entry=make_slice(a.owner_dol)
    a.output.write_bytes(payload)
    print(f'PRIVATE test-only DOL: entry=0x{entry:08X}, stop=0x{STOP_PC:08X}, length={len(payload)}')

if __name__=='__main__':main()
