#!/usr/bin/env python3
"""Authenticate the original interrupt-enable leaf and exact mtmsr resume."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl
ENTRY=0x805265c0;CALL=0x80520944
def geometry(words):
    if len(words)!=5 or words[-1]!=0x4e800020:raise ValueError('leaf extent')
    mf=[i for i,w in enumerate(words) if w>>26==31 and (w>>1)&1023==83]
    mt=[i for i,w in enumerate(words) if w>>26==31 and (w>>1)&1023==146]
    if len(mf)!=1 or len(mt)!=1 or not mf[0]<mt[0]<4:raise ValueError('MSR geometry')
    if any(w>>26 in (16,17,18) or w>>26==19 and w!=0x4e800020 for w in words):raise ValueError('not a leaf')
    return ENTRY+4*(mt[0]+1)
def build(words):
    resume=geometry(words);raw=struct.pack('>5I',*words);h=bytearray(256)
    for off,v in ((0,256),(0x48,ENTRY),(0x90,len(raw)),(0xe0,ENTRY)):struct.pack_into('>I',h,off,v)
    return bytes(h)+raw,resume
def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--owner',type=Path);a=p.parse_args()
    try:
        if a.owner:
            if a.owner.stat().st_size>MAX_DOL:raise ValueError('size')
            d=a.owner.read_bytes()
            if hashlib.sha256(d).hexdigest()!=OWNER_SHA or direct_bl(words_at(d,CALL,1)[0],CALL)!=ENTRY:raise ValueError('identity')
            words=words_at(d,ENTRY,5)
        else:
            # Independent implementation with distinct temporaries:
            # mfmsr r4; ori r5,r4,0x8000; mtmsr r5; extract old EE; blr.
            words=((31<<26)|(4<<21)|(83<<1),(24<<26)|(4<<21)|(5<<16)|0x8000,
                   (31<<26)|(5<<21)|(146<<1),(21<<26)|(4<<21)|(3<<16)|(17<<11)|(31<<6)|(31<<1),0x4e800020)
        raw,resume=build(words);a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(raw)
        (a.out/'symbols.csv').write_text('Name,Location,Size\nfunc_805265C0,805265c0,20\n')
        (a.out/'v613_expected.h').write_text(f'#pragma once\ninline constexpr uint32_t Resume=0x{resume:08x}u;\n')
    except (OSError,ValueError,struct.error):print('V613_IRQ_FIXTURE accepted=0');return 1
    print(f'V613_IRQ_FIXTURE owner={int(a.owner is not None)} accepted=1 leaf=1');return 0
if __name__=='__main__':raise SystemExit(main())
