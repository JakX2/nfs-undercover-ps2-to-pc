#!/usr/bin/env python3
"""Install first nested direct helper on the authenticated second-helper route."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v625_ipc_client import audit_native
from prepare_v574_dsp_sc import diagnostic
from prepare_v680_si_helper import patch_helper,verify_direct
from si_nested_geometry_v693 import nested_plan
def patch_second(s):
    for a,b in (
        ('#include "v688_private_si_second_expectations.h"','#include "v688_private_si_second_expectations.h"\n#include "wii_si_nested_binding_v693.h"'),
        ('    if(second.stage()!=1)return false;','    if(v693::observe(a,c))return true;\n    if(second.stage()!=1)return false;'),
        ('    if(!second.instruction(c,pc,word,si_completion_ack_trace,true)){',
         '    v693::boundary(c,pc);\n    const bool allow=v693::eligible(pc,word,ordinal,kind);\n    if(!second.instruction(c,pc,word,si_completion_ack_trace,true,allow)){'),
        ('    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){',
         '    if(allow&&si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Armed){v693::start(c,pc,word);return;}\n    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){')):
        s=replace_exact(s,a,b)
    return s
def install(dol,elf,root,host):
    site,target,size,word,words=nested_plan(dol,elf)
    shards=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('nested tree')
    changes={};seen={};calls=entries=0
    for p in shards:
        s=p.read_text(encoding='utf-8')
        if re.search(r'(?mi)^loc_'+f'{site:X}'+r': ;$',s):verify_direct(s,site,target);calls+=1
        entries+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);')
        new,found=patch_helper(s,target,words,nested=True)
        if found:
            if seen:raise ValueError('nested duplicate root')
            seen=found;changes[p]=new
    if calls!=1 or entries!=1 or len(seen)!=len(words):raise ValueError('nested route coverage')
    n=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),seen)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/'wii_si_nested_binding_v693.h':(host/'wii_si_nested_binding_v693.h').read_text(encoding='utf-8')}
    files[dest/'v693_private_si_nested_expectations.h']='#pragma once\n#include "wii_si_first_helper_v680.h"\nnamespace undercover::wii::v693 {\ninline constexpr SiHelperExpectation expected_nested{'+','.join(f'0x{x:08x}u' for x in (site,target,target+size,word))+'};\n}\n'
    bind=dest/'wii_si_second_binding_v688.h'
    if dest.is_symlink() or bind.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('nested destination')
    files[bind]=patch_second(bind.read_text(encoding='utf-8'))
    for p,s in {**changes,**files}.items():p.write_text(s,encoding='utf-8')
    return n
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V693_SI_NESTED_ROUTE installed=0');return 1
    print(f'V693_SI_NESTED_ROUTE installed=1 native_labels={n} first_edge=1 deeper_guard=3 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
