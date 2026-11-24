#!/usr/bin/env python3
"""Extend the complete-image V419 trace to authenticated PS/FPR/cache entry."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import (OWNER_SHA,MAX_DOL,HW,words_at,direct_bl,expectations,prepare,replace_exact)

PS=0x80520fb4;HIDR=0x804b79dc;HIDW=0x804b79e4;IC=0x805223ac;FPR=0x8051fbb0;CACHE=0x80522540
ENTRIES=((PS,HW+20,21),(HIDR,PS+16,2),(HIDW,PS+24,2),(IC,PS+28,4),(FPR,HW+24,74),(CACHE,HW+28,4))
MICRO='void micro_interpret(CPUContext& ctx, uint32_t opcode, uint32_t pc) {'
MICRO_NEW=MICRO+'\n  if (undercover::wii::v419::enabled()) undercover::wii::v419::reject_interpreter();'

def hardware_expectations(data:bytes,digest:str=OWNER_SHA)->str:
    expectations(data,digest)
    hw=words_at(data,HW,9);ps=words_at(data,PS,21)
    if hw[-1]!=0x4e800020 or ps[-1]!=0x4e800020:raise ValueError('hardware return geometry')
    for i,pc in ((4,PS),(5,FPR),(6,CACHE)):
        if direct_bl(hw[i],HW+4*i)!=pc:raise ValueError('hardware call geometry')
    for i,pc in ((3,HIDR),(5,HIDW),(6,IC)):
        if direct_bl(ps[i],PS+4*i)!=pc:raise ValueError('PS call geometry')
    rows=[]
    for pc,lr,count in ENTRIES:
        words=words_at(data,pc,count)
        if pc!=CACHE and words[-1]!=0x4e800020:raise ValueError('return geometry')
        if pc==FPR and (words[8]>>26!=56 or words[40]>>26!=50 or ((words[72]>>1)&1023)!=711):raise ValueError('FPR geometry')
        rows.append(f'HardwareEntry{{0x{pc:08x}u,0x{lr:08x}u,{count}u,{{'+', '.join(f'0x{w:08x}u' for w in words)+'}}')
    return ('#pragma once\n#include "wii_full_hardware_witness.h"\nnamespace undercover::wii::v425 {\n'
            'inline constexpr HardwareExpectations expected_hardware{{\n'+',\n'.join(rows)+'\n},0x8070db08u,0x8070db10u};\n}\n')

def install(data:bytes,generated:Path,host:Path,digest:str=OWNER_SHA)->None:
    expected=hardware_expectations(data,digest)
    counts=dict.fromkeys((pc for pc,_,_ in ENTRIES),0)
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:
            needle=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);'
            counts[pc]+=source.count(needle)
    if any(n!=1 for n in counts.values()):raise ValueError('native hardware trace missing')
    rt=generated/'nWiiRuntime';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include/undercover'
    if interp.is_symlink():raise ValueError('interpreter symlink')
    replace_exact(interp.read_text(encoding='utf-8'),MICRO,MICRO_NEW)
    files={dest/'v425_private_hardware_expectations.h':expected,
           dest/'wii_full_hardware_witness.h':(host/'wii_full_hardware_witness.h').read_text(encoding='utf-8')}
    if any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=(host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8')
    prepare(data,generated,host,digest)
    updated=replace_exact(interp.read_text(encoding='utf-8'),MICRO,MICRO_NEW)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8')
    interp.write_text(updated,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('DOL size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V425_HARDWARE_ROUTE installed=0');return 1
    print('V425_HARDWARE_ROUTE installed=1 cap=9 interpreter_reject=1 micro_reject=1');return 0
if __name__=='__main__':raise SystemExit(main())
