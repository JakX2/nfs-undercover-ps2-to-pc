#!/usr/bin/env python3
"""Prepare a bounded startup observer in a private complete-image C++ project."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

OWNER_SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY=0x8000403c;REG=0x800041a8;HW=0x800042e0
EXPECTED_GPRS=tuple({1:0x80751cb8,2:0x80715ee0,13:0x8070e8e0}.get(i,0) for i in range(32))
HEADER='#include "runtime/cpu_context.h"'
INCLUDE=HEADER+'\n#include "undercover/wii_full_start_probe_v419.h"'
TRACE='void trace_call(uint32_t func_addr, CPUContext &ctx) {'
TRACE_NEW=TRACE+'''
  if (undercover::wii::v419::enabled()) {
    undercover::wii::v419::observe(func_addr, ctx);
    return;
  }'''
INTERPRET='void interpret_step(CPUContext& ctx) {'
INTERPRET_NEW=INTERPRET+'\n  if (undercover::wii::v419::enabled()) undercover::wii::v419::reject_interpreter();'
MAX_DOL=32*1024*1024

def u32(data:bytes,at:int)->int:return struct.unpack_from('>I',data,at)[0]
def words_at(data:bytes,pc:int,n:int)->tuple[int,...]:
    if pc&3 or n<=0 or n>1024:raise ValueError('text request')
    matches=[]
    for i in range(7):
        off,base,size=(u32(data,b+4*i) for b in (0,0x48,0x90))
        if not size:continue
        if off<256 or off+size>len(data) or base+size>2**32:raise ValueError('text geometry')
        if base<=pc and pc+4*n<=base+size:
            matches.append(struct.unpack_from('>'+str(n)+'I',data,off+pc-base))
    if len(matches)!=1:raise ValueError('text mapping')
    return matches[0]

def direct_bl(word:int,pc:int)->int:
    if word>>26!=18 or word&3!=1:raise ValueError('linked branch')
    disp=word&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    return (pc+disp)&0xffffffff

def expectations(data:bytes,digest:str=OWNER_SHA)->str:
    if not 256<=len(data)<=MAX_DOL or hashlib.sha256(data).hexdigest()!=digest or u32(data,0xe0)!=ENTRY:raise ValueError('owner identity')
    entry=words_at(data,ENTRY,2);register=words_at(data,REG,36);hardware=words_at(data,HW,4)
    if direct_bl(entry[0],ENTRY)!=REG or direct_bl(entry[1],ENTRY+4)!=HW or register[-1]!=0x4e800020:raise ValueError('startup geometry')
    fmt=lambda values:'{'+', '.join(f'0x{v:08x}u' for v in values)+'}'
    return ('#pragma once\n#include "wii_full_start_witness.h"\nnamespace undercover::wii::v419 {\n'
            f'inline constexpr FullStartExpectations expected{{0x{ENTRY:08x}u,0x{REG:08x}u,0x{HW:08x}u,\n'
            +',\n'.join(fmt(v) for v in (entry,register,hardware,EXPECTED_GPRS))+'};\n}\n')

def replace_exact(source:str,old:str,new:str)->str:
    if source.count(old)!=1 or new in source:raise ValueError('source seam')
    return source.replace(old,new,1)

def patch(source:str,old:str,new:str)->str:
    if 'undercover::wii::v419::' in source or INCLUDE in source:raise ValueError('already patched')
    result=replace_exact(replace_exact(source,HEADER,INCLUDE),old,new)
    if result.replace(new,old,1).replace(INCLUDE,HEADER,1)!=source:raise ValueError('source seam')
    return result

def prepare(data:bytes,generated:Path,host:Path,digest:str=OWNER_SHA)->None:
    expected=expectations(data,digest)
    # Require exactly one real generated AOT trace seam at each original
    # entry, not merely a dispatcher/HLE function declaration.
    counts=dict.fromkeys((ENTRY,REG,HW),0)
    shards=list(generated.glob('output_*.cpp'))
    if not shards:raise ValueError('generated shards')
    for shard in shards:
        content=shard.read_text(encoding='utf-8')
        for pc in counts:
            needle=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);'
            counts[pc]+=content.count(needle)
    if any(v!=1 for v in counts.values()):raise ValueError('native entry trace missing')
    rt=generated/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interpreter=rt/'src/hle/interpreter.cpp';dest=rt/'include/undercover'
    updates={stubs:patch(stubs.read_text(encoding='utf-8'),TRACE,TRACE_NEW),interpreter:patch(interpreter.read_text(encoding='utf-8'),INTERPRET,INTERPRET_NEW)}
    files={dest/'v419_private_start_expectations.h':expected}
    for name in ('wii_full_start_witness.h','wii_full_start_probe_v419.h'):files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.is_symlink() for p in updates) or any(p.exists() or p.is_symlink() for p in files):raise ValueError('private destination exists')
    dest.mkdir(exist_ok=True)
    for p,s in {**updates,**files}.items():p.write_text(s,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('DOL size')
        prepare(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V419_FULL_START_ROUTE installed=0');return 1
    print('V419_FULL_START_ROUTE installed=1 original_entry=1 cap=3 interpreter_reject=1');return 0
if __name__=='__main__':raise SystemExit(main())
