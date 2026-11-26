#!/usr/bin/env python3
"""Privately enumerate bounded writable ELF objects of SDK heap-table size."""
import argparse,hashlib
from pathlib import Path
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL,ORIGINAL_SHA256,parse_functions

def candidates(data):
    parse_functions(data) # validates ELF32/PPC header and symbol tables
    head=HEADER.unpack_from(data);off,num=head[6],head[12]
    sections=[SECTION.unpack_from(data,off+i*SECTION.size) for i in range(num)]
    out=set()
    for s in sections:
        if s[1]!=2:continue
        for pos in range(s[4],s[4]+s[5],SYMBOL.size):
            _,addr,size,info,_,idx=SYMBOL.unpack_from(data,pos)
            if info&15!=1 or size!=128 or not 0<idx<len(sections):continue
            sec=sections[idx]
            if sec[2]&3!=3 or not sec[3]<=addr or addr+size>sec[3]+sec[5]:continue
            if addr&3 or not 0x80000000<=addr<=0x81800000-size:continue
            out.add(addr)
    if not 0<len(out)<=1024:raise ValueError('candidate count')
    if any(a+128>b for a,b in zip(sorted(out),sorted(out)[1:])):raise ValueError('overlap')
    return sorted(out)

def main():
    p=argparse.ArgumentParser();p.add_argument('elf',type=Path);p.add_argument('header',type=Path);a=p.parse_args()
    try:
        if not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        raw=a.elf.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        rows=candidates(raw)
        with a.header.open('x') as f:
            f.write('#pragma once\n#include "wii_allocator_descriptor_v1356.h"\nnamespace v1356 {\ninline constexpr std::array<undercover::wii::AllocatorRange,'+str(len(rows))+'> tables{'+','.join('undercover::wii::AllocatorRange{0x%08xu,128u}'%x for x in rows)+'};\n}\n')
        print(f'V1356_DESCRIPTOR_CANDIDATES verified=1 count={len(rows)}')
        return 0
    except (OSError,ValueError,IndexError):
        print('V1356_DESCRIPTOR_CANDIDATES verified=0');return 1
if __name__=='__main__':raise SystemExit(main())
