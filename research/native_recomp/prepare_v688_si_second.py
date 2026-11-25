#!/usr/bin/env python3
"""Instrument only the newly observed second original SI helper."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v625_ipc_client import audit_native
from prepare_v574_dsp_sc import diagnostic
from prepare_v680_si_helper import patch_helper,verify_direct,exact_function
from si_second_geometry_v688 import second_plan
from prepare_v668_si_ack import HANDLER
def patch_binding(s):
    for a,b in (
        ('#include "wii_si_helper_binding_v680.h"','#include "wii_si_second_binding_v688.h"'),
        ('    v680::handler_boundary(c,pc);','    v680::handler_boundary(c,pc);\n    v688::handler_boundary(c,pc);'),
        ('        if(v680::start(c,pc,word,ordinal,kind))return;','        if(v680::start(c,pc,word,ordinal,kind)||v688::start(c,pc,word,ordinal,kind))return;'),
        ('if(v680::observe(a,c))return;','if(v680::observe(a,c)||v688::observe(a,c))return;')):
        s=replace_exact(s,a,b)
    return s
def install(dol,elf,generated,host):
    site,target,size,word,words=second_plan(dol,elf)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('second helper tree')
    changes={};seen={};calls=entries=0
    for p in shards:
        s=p.read_text(encoding='utf-8')
        if re.search(r'(?mi)^loc_'+f'{site:X}'+r': ;$',s):verify_direct(s,site,target);calls+=1
        entries+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);')
        new,found=patch_helper(s,target,words,True)
        if found:
            if seen:raise ValueError('second helper duplicate root')
            seen=found;changes[p]=new
    if calls!=1 or entries!=1 or len(seen)!=len(words):raise ValueError('second helper route coverage')
    native=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),seen)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'wii_si_second_binding_v688.h':(host/'wii_si_second_binding_v688.h').read_text(encoding='utf-8')}
    files[dest/'v688_private_si_second_expectations.h']='#pragma once\n#include "wii_si_first_helper_v680.h"\nnamespace undercover::wii::v688 {\ninline constexpr SiHelperExpectation expected_second{'+','.join(f'0x{x:08x}u' for x in (site,target,target+size,word))+'};\n}\n'
    bind=dest/'wii_si_ack_binding_v672.h'
    if dest.is_symlink() or bind.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('second helper destination')
    files[bind]=patch_binding(bind.read_text(encoding='utf-8'))
    for p,s in {**changes,**files}.items():p.write_text(s,encoding='utf-8')
    return native
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V688_SI_SECOND_ROUTE installed=0');return 1
    print(f'V688_SI_SECOND_ROUTE installed=1 native_labels={n} nested_guard=2 actual_mmio=1 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
