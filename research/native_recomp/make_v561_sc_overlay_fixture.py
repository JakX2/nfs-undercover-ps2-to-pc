#!/usr/bin/env python3
"""Build an independent synthetic caller and either synthetic or private original SC source.
All private bytes and generated code stay inside the private runner.
"""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl
SOURCE=0x805290a8
ENTRY=0x80004000
FLUSH=0x805222c0
def build(vector,flush=None):
    if len(vector)!=28:raise ValueError('vector size')
    # li r4,7; sc; addi r4,r4,3; blr
    caller=struct.pack('>4I',0x38800007,0x44000002,0x38840003,0x4e800020)
    if flush is not None:
        if len(flush)!=48:raise ValueError('flush size')
        caller=flush
    entry=ENTRY if flush is None else FLUSH
    header=bytearray(256)
    for i,(a,body,off) in enumerate(((entry,caller,256),(SOURCE,vector,256+len(caller)))):
        for h,v in ((0,off),(0x48,a),(0x90,len(body))):struct.pack_into('>I',header,h+4*i,v)
    struct.pack_into('>I',header,0xe0,entry)
    return bytes(header)+caller+vector
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--owner',type=Path);p.add_argument('--flush',action='store_true');p.add_argument('--binding',action='store_true');p.add_argument('--arena',action='store_true');a=p.parse_args()
    try:
        if (a.binding or a.arena) and not a.flush:raise ValueError('binding requires flush')
        if a.arena and not a.binding:raise ValueError('arena requires ABI fixture')
        if a.owner:
            if a.owner.stat().st_size>MAX_DOL:raise ValueError('size')
            raw=a.owner.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=OWNER_SHA:raise ValueError('identity')
            vector=struct.pack('>7I',*words_at(raw,SOURCE,7))
        elif a.binding:
            # Independently assembled ABI control: read HID0, compute its
            # bit-3-set value in r10, order, no HID0 write, then return.
            spr=1008
            mfspr=(31<<26)|(9<<21)|((spr&31)<<16)|((spr>>5)<<11)|(339<<1)
            ori=(24<<26)|(9<<21)|(10<<16)|8
            vector=struct.pack('>7I',mfspr,ori,0x7c0004ac,0x4c00012c,0x60000000,0x60000000,0x4c000064)
        else:
            # Independent fixture, changes r11 but does not touch HID0.
            vector=struct.pack('>7I',0x396b0001,0x4c00012c,*([0x60000000]*4),0x4c000064)
        flush=None
        if a.flush:
            if a.owner:
                if a.arena:
                    for site in (0x80520028,0x80520204):
                        if direct_bl(words_at(raw,site,1)[0],site)!=FLUSH:raise ValueError('arena flush callsite')
                w=words_at(raw,FLUSH,12)
                if w[-2:]!=(0x44000002,0x4e800020):raise ValueError('flush SC return geometry')
            elif a.arena:
                # Independent counted native loop for any nonzero aligned size.
                # srwi r4,r4,5; mtctr r4; dcbf 0,r3; addi r3,r3,32;
                # bdnz to dcbf; pad to the authenticated SC/BLR seam.
                shift=(21<<26)|(4<<21)|(4<<16)|(27<<11)|(5<<6)|(31<<1)
                mtctr=(31<<26)|(4<<21)|(9<<16)|(467<<1)
                w=(shift,mtctr,0x7c0018ac,0x38630020,0x4200fff8,*([0x60000000]*5),0x44000002,0x4e800020)
            else:
                # Independent straight-line dcbf fixture, four lines from r3.
                w=(0x7c0018ac,0x38630020,0x7c0018ac,0x38630020,
                   0x7c0018ac,0x38630020,0x7c0018ac,0x60000000,
                   0x60000000,0x60000000,0x44000002,0x4e800020)
            flush=struct.pack('>12I',*w)
        a.output.mkdir(mode=0o700)
        (a.output/'fixture.dol').write_bytes(build(vector,flush))
        (a.output/'vector.bin').write_bytes(vector)
        if a.binding:
            header='#pragma once\n#include <array>\n#include <cstdint>\nnamespace undercover::wii::v574 {\ninline constexpr std::array<uint8_t,28> expected_vector{'+','.join(map(str,vector))+'};\ninline constexpr uint32_t return_word=0x60000000u;\n}\n'
            (a.output/'v574_private_sc_expectations.h').write_text(header,encoding='utf-8')
        symbol='func_805222C0,805222c0,48' if a.flush else 'func_80004000,80004000,16'
        (a.output/'symbols.csv').write_text('Name,Location,Size\n'+symbol+'\n',encoding='utf-8')
        print(f'V561_SC_FIXTURE owner={int(a.owner is not None)} bytes=28')
        return 0
    except (OSError,ValueError,struct.error):
        print('V561_SC_FIXTURE accepted=0');return 1
if __name__=='__main__':raise SystemExit(main())
