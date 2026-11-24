#!/usr/bin/env python3
"""Build an independent synthetic caller and either synthetic or private original SC source.
All private bytes and generated code stay inside the private runner.
"""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at
SOURCE=0x805290a8
ENTRY=0x80004000
def build(vector):
    if len(vector)!=28:raise ValueError('vector size')
    # li r4,7; sc; addi r4,r4,3; blr
    caller=struct.pack('>4I',0x38800007,0x44000002,0x38840003,0x4e800020)
    header=bytearray(256)
    for i,(a,body,off) in enumerate(((ENTRY,caller,256),(SOURCE,vector,272))):
        for h,v in ((0,off),(0x48,a),(0x90,len(body))):struct.pack_into('>I',header,h+4*i,v)
    struct.pack_into('>I',header,0xe0,ENTRY)
    return bytes(header)+caller+vector
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--owner',type=Path);a=p.parse_args()
    try:
        if a.owner:
            if a.owner.stat().st_size>MAX_DOL:raise ValueError('size')
            raw=a.owner.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=OWNER_SHA:raise ValueError('identity')
            vector=struct.pack('>7I',*words_at(raw,SOURCE,7))
        else:
            # Independent fixture, changes r11 but does not touch HID0.
            vector=struct.pack('>7I',0x396b0001,*([0x60000000]*5),0x4c000064)
        a.output.mkdir(mode=0o700)
        (a.output/'fixture.dol').write_bytes(build(vector))
        (a.output/'vector.bin').write_bytes(vector)
        (a.output/'symbols.csv').write_text('Name,Location,Size\nfunc_80004000,80004000,16\n',encoding='utf-8')
        print(f'V561_SC_FIXTURE owner={int(a.owner is not None)} bytes=28')
        return 0
    except (OSError,ValueError,struct.error):
        print('V561_SC_FIXTURE accepted=0');return 1
if __name__=='__main__':raise SystemExit(main())
