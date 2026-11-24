#!/usr/bin/env python3
"""Build a private original reset-code query fixture or independent PPC control."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl
ENTRY=0x805285d0
def build(words):
    if len(words)!=12 or words[-1]!=0x4e800020:raise ValueError('reset function extent')
    raw=struct.pack('>12I',*words);h=bytearray(256)
    for off,v in ((0,256),(0x48,ENTRY),(0x90,len(raw)),(0xe0,ENTRY)):
        struct.pack_into('>I',h,off,v)
    return bytes(h)+raw
def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--owner',type=Path);a=p.parse_args()
    try:
        if a.owner:
            if a.owner.stat().st_size>MAX_DOL:raise ValueError('size')
            d=a.owner.read_bytes()
            if hashlib.sha256(d).hexdigest()!=OWNER_SHA:raise ValueError('identity')
            for site in (0x8051ffdc,0x805201b8):
                if direct_bl(words_at(d,site,1)[0],site)!=ENTRY:raise ValueError('original caller')
            words=words_at(d,ENTRY,12)
        else:
            # Independent cold path: lis r3,0xcc00; lwz r3,0x3024(r3);
            # srwi r3,r3,3; padding; blr.
            shift=(21<<26)|(3<<21)|(3<<16)|(29<<11)|(3<<6)|(31<<1)
            words=(0x3c60cc00,0x80633024,shift,*([0x60000000]*8),0x4e800020)
        if any(w>>26==17 or (w>>26==18 and w&1) for w in words):raise ValueError('not a leaf')
        a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(build(words))
        (a.out/'symbols.csv').write_text('Name,Location,Size\nfunc_805285D0,805285d0,48\n')
    except (OSError,ValueError,struct.error):print('V610_RESET_FIXTURE accepted=0');return 1
    print(f'V610_RESET_FIXTURE owner={int(a.owner is not None)} accepted=1 leaf=1');return 0
if __name__=='__main__':raise SystemExit(main())
