#!/usr/bin/env python3
"""Original-only SIInit initialized-word store location classification.

No original instructions, addresses, register contents, or owner input are
printed. This is static evidence; it is not a runtime startup proof.
"""
import argparse
import hashlib
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl
from make_start_to_si_sampling_v58 import SI
from make_start_to_si_return_v59 import SI_END,TYPE
FIRST=0x8053210c
LAST=0x80532124
FLAG=-3148
def classify(data,digest=OWNER_SHA):
    if not 256<=len(data)<=MAX_DOL or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('identity')
    words=words_at(data,SI,(SI_END-SI)//4)
    for pc in range(FIRST,LAST+1,8):
        if direct_bl(words[(pc-SI)//4],pc)!=TYPE:raise ValueError('query geometry')
    if words[-1]!=0x4e800020:raise ValueError('return geometry')
    stores=[]
    for i,w in enumerate(words):
        # stw rS,d(r13), exact signed D-form displacement.
        if w>>26==36 and (w>>16)&31==13 and w&0xffff==FLAG&0xffff:
            stores.append(SI+4*i)
    if len(stores)!=1:return 'ambiguous',len(stores)
    pc=stores[0]
    return ('before' if pc<FIRST else 'after' if pc>LAST else 'between'),1
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        relation,count=classify(a.dol.read_bytes())
        print(f'V544_SI_FLAG_STATIC stores={count} relation={relation} boot_verified=0')
        return 0 if count==1 else 1
    except (OSError,ValueError,struct.error):
        print('V544_SI_FLAG_STATIC inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
