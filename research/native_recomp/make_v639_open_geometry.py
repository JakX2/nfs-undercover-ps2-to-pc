#!/usr/bin/env python3
"""Derive private first IOS_Open request construction geometry."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,direct_bl
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from make_v624_ipc_geometry import exact_words
from make_start_to_ios_open_v71 import OPEN,SIZE,PROFILE,ALLOC,ALLOC_SIZE,STOP,EDGES
from prepare_v629_stm_open import geometry as stm_geometry
SPANS=((OPEN,SIZE),(PROFILE,4),(ALLOC,ALLOC_SIZE),(0x805222c0,48))
CALLS=((0x8052b08c,OPEN),EDGES[0],(0x8051ab60,0x805265ac),(0x8051ad10,0x805265d4),EDGES[1],EDGES[2])
def geometry(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    stm_geometry(dol,elf,dd,ed);sizes=parse_functions(elf)
    blocks={}
    for pc,n in SPANS:
        if sizes.get(pc)!=n:raise ValueError('open extent')
        blocks[pc]=exact_words(dol,elf,pc,n//4)
    tail=blocks[PROFILE][0];disp=tail&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    if tail>>26!=18 or tail&3 or (PROFILE+disp)&0xffffffff!=ALLOC:raise ValueError('allocator tail')
    if blocks[ALLOC][-1]!=0x4e800020 or blocks[0x805222c0][-2:]!=(0x44000002,0x4e800020):raise ValueError('return geometry')
    rows=[]
    for site,target in CALLS:
        w=exact_words(dol,elf,site,1)[0]
        if direct_bl(w,site)!=target or not sizes.get(target):raise ValueError('open edge')
        rows.append((target,site+4,w,exact_words(dol,elf,target,1)[0]))
    extra=(blocks[ALLOC][0],blocks[0x805222c0][-2],exact_words(dol,elf,0x80519a1c,1)[0])
    return rows,extra,blocks
def render(g):
    rows,extra,_=g
    fmt=lambda seq:','.join(f'0x{v:08x}u' for v in seq)
    return ('#pragma once\n#include "wii_open_request_witness_v639.h"\nnamespace undercover::wii::v639 {\n'
        'inline constexpr OpenRequestExpectations expected_open{'+','.join('VectorEdge{'+fmt(x)+'}' for x in rows)+','+fmt(extra)+'};\n}\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('--private-header',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        g=geometry(a.dol.read_bytes(),a.elf.read_bytes())
        if a.private_header:
            with a.private_header.open('x',encoding='utf-8') as f:f.write(render(g))
    except (OSError,ValueError,struct.error) as e:
        why=str(e) if str(e) in {'size','open extent','allocator tail','return geometry','open edge','word identity','identity'} else 'prior_or_io'
        print('V639_OPEN_GEOMETRY accepted=0 reason='+why.replace(' ','_'));return 1
    print('V639_OPEN_GEOMETRY owner=1 accepted=1 spans=4 edges=6 tail=1 exact_dol_elf=1');return 0
if __name__=='__main__':raise SystemExit(main())
