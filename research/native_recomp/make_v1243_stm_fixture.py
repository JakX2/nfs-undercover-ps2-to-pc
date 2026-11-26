#!/usr/bin/env python3
"""Private focused original IPC + STM prefix; no original data is exported."""
import argparse
import re
import struct
from pathlib import Path
from make_v626_ipc_fixture import build as ipc_build,assemble
from make_v624_ipc_geometry import ROOT
from prepare_v629_stm_open import geometry as stm_geometry,render as stm_render,BEGIN,STM,OPEN,PATHS,FIRST_OPEN_CALL
from prepare_v419_full_start import words_at,MAX_DOL
BLR=0x4e800020
SDA={2:0x80715ee0,13:0x8070e8e0}

def data_at(dol,addr,n):
    if n<=0 or not 0x80000000<=addr<addr+n<=0x81800000:raise ValueError('STM data range')
    hits=[]
    for i in range(11):
        off,base,size=(struct.unpack_from('>I',dol,k+4*i)[0] for k in (0x1c,0x64,0xac))
        if not size:continue
        if off<256 or off+size>len(dol) or base+size>2**32:raise ValueError('STM data section')
        if base<=addr and addr+n<=base+size:hits.append(dol[off+addr-base:off+addr-base+n])
    if len(hits)>1:raise ValueError('STM data overlap')
    return hits[0] if hits else None

def seed_data(dol,prefix,paths):
    out={}
    def add(addr,blob):
        for i,v in enumerate(blob):
            if addr+i in out and out[addr+i]!=v:raise ValueError('STM data identity')
            out[addr+i]=v
    for w in prefix:
        major=w>>26;ra=(w>>16)&31
        if major not in (32,34,40) or ra not in SDA:continue
        disp=w&0xffff
        if disp&0x8000:disp-=0x10000
        addr=SDA[ra]+disp;n={32:4,34:1,40:2}[major]
        blob=data_at(dol,addr,n)
        if blob is not None:add(addr,blob)
    for addr,kind in paths:
        if kind not in (1,2):raise ValueError('STM path kind')
        blob=PATHS[kind-1]
        if data_at(dol,addr,len(blob))!=blob:raise ValueError('STM data identity')
        add(addr,blob)
    if not out or len(out)>512:raise ValueError('STM seed size')
    return out

def extend(raw,csv,stm,op,prefix):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if not re.fullmatch(r'func_[0-9A-F]{8}',name) or not size or size%4 or pc in blocks:
            raise ValueError('STM fixture symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if stm in blocks or op[0] in blocks or len(prefix)!=23:raise ValueError('STM fixture roots')
    # Both synthetic BLRs are unreachable in the admitted test. They
    # only delimit the isolated generated symbols for the compiler.
    blocks[stm]=tuple(prefix)+(BLR,)
    blocks[op[0]]=(op[3],BLR)
    symbols='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble(blocks,ROOT),symbols

def build(dol,elf):
    raw,csv,ipc,image=ipc_build(dol,elf)
    g=stm_geometry(dol,elf)
    bridge,body,stm,op,paths,_=g
    prefix=body[:(FIRST_OPEN_CALL-STM)//4+1]
    raw,csv=extend(raw,csv,STM,op,prefix)
    data=seed_data(dol,prefix,paths)
    words={BEGIN+4*i:w for i,w in enumerate(bridge)}
    words.update({STM+4*i:w for i,w in enumerate(prefix)})
    words[OPEN]=op[3]
    fmt=lambda v:f'0x{v:08x}u'
    header=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v1243 {\n'
            'struct Word {uint32_t pc,word;}; struct Byte {uint32_t addr;uint8_t value;};\n'
            'inline constexpr std::array<Word,'+str(len(words))+'> words{'
            +','.join('Word{'+fmt(k)+','+fmt(v)+'}' for k,v in sorted(words.items()))+'};\n'
            'inline constexpr std::array<Byte,'+str(len(data))+'> data{'
            +','.join('Byte{'+fmt(k)+','+str(v)+'}' for k,v in sorted(data.items()))+'};\n}\n')
    return raw,csv,ipc,image,stm_render(g),header

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        raw,csv,ipc,image,stm,header=build(a.dol.read_bytes(),a.elf.read_bytes())
        a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(raw)
        for name,data in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v626_private_words.h',image),
                          ('v629_private_stm_expectations.h',stm),('v1243_private_stm_data.h',header)):
            (a.out/name).write_text(data)
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1243_STM_FIXTURE accepted=0');return 1
    print('V1243_STM_FIXTURE accepted=1 owner=1 prefix=23 open_entry=1 synthetic_boundaries=2')
    return 0
if __name__=='__main__':raise SystemExit(main())
