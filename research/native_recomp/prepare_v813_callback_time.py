#!/usr/bin/env python3
"""Compose original callback continuation and reused OS time leaves privately."""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_callback_time_v802 import plan
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v807_callback_prefix import patch_label,SI
from prepare_v667_si_dispatch import exact

def render(C,ts,continuation,T,system,leaves):
    fmt=lambda ws:','.join(f'0x{w:08x}u' for w in ws)
    resume=ts-4*(len(continuation)-2)
    return ('#pragma once\n#include "wii_callback_time_v810.h"\nnamespace undercover::wii::v813 {\n'
            f'inline constexpr std::array<uint32_t,{len(continuation)}> continuation{{'+fmt(continuation)+'};\n'
            f'inline constexpr std::array<uint32_t,{len(system)}> system_words{{'+fmt(system)+'};\n'
            'inline constexpr CallbackTimeExpectation expected{'+fmt((C,C+688,resume,ts,T))+
            ',continuation,system_words,{{'+','.join('PostAckLeafExpectation{'+fmt(row[:4])+f',{row[4]}u'+'}' for row in leaves)
            +'}},0x800030d8u};\n}\n')

def patch_prefix(s):
    a='#include "wii_callback_dispatch_device_v808.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_time_binding_v813.h"')
    a='<<" continuation_executed=0 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','if(v813::enabled()){v813::start(c,pc,w,route.stage()==6);return;}std::_Exit(0);'))

def patch_ack(s):
    a='    if(v807::active())return v807::poll(c);'
    s=replace_exact(s,a,'    if(v813::active())return v813::poll(c);\n'+a)
    a='if(v807::observe(a,c))return;'
    return replace_exact(s,a,'if(v813::observe(a,c))return;'+a)

def patch_shared(s,leaf=False):
    a='#include "wii_alarm_return_binding_v786.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_time_binding_v813.h"')
    a='    if(v786::active()){v786::before(c,pc,word);return;}'
    return replace_exact(s,a,'    if(v813::active()){v813::before(c,pc,word);return;}\n'+a)

def patch_callback_label(s,pc,w):
    # Same validated scheduler seam as V807, but distinct time route.
    return patch_label(s,pc,w).replace(
        f'undercover::wii::v807::before(ctx,0x{pc:08x}u,0x{w:08x}u);',
        f'undercover::wii::v813::before(ctx,0x{pc:08x}u,0x{w:08x}u);')

def verify_order(body,pc,w,namespace):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n.*?(?=^loc_[0-9a-f]+: ;|\Z)',re.S|re.M)
    m=list(pat.finditer(body))
    if len(m)!=1:raise ValueError('shared time label')
    block=m[0][0]
    hook=f'undercover::wii::{namespace}::before(ctx,'
    if block.count(SI)!=1 or block.count(hook)!=1 or block.index(SI)>block.index(hook):
        raise ValueError('shared time scheduler order')

def install(dol,elf,root,host):
    q,T,D,U,R,ts,leaves=plan(dol,elf);roots,C,S,site,_,_=q
    resume=site+4;continuation=roots[C][(resume-C)//4:-1]
    original=exact(dol,elf,C,172)
    if tuple(continuation)!=original[(resume-C)//4:(ts-C)//4+2] or len(roots[T])!=25:
        raise ValueError('callback time identity')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('callback time tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    def owner(a):
        found=[p for p,s in src.items() if owns_root(s,a)]
        if len(found)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('callback time owner')
        return found[0]
    cp=owner(C)
    body=exact_function(src[cp],C)
    verify_direct(body,ts,T)
    pcs={pc for pc in reachable(C,roots[C]) if resume<=pc<=ts+4}
    if resume not in pcs or ts+4 not in pcs:raise ValueError('callback time coverage')
    expected={pc:(C,original[(pc-C)//4]) for pc in pcs}
    for a in (T,D,U,R):
        p=owner(a);b=exact_function(src[p],a)
        if a==T:
            for row in leaves:verify_direct(b,row[0],row[1])
        for pc in reachable(a,roots[a]):
            w=roots[a][(pc-a)//4]
            if pc in expected:raise ValueError('callback time overlap')
            expected[pc]=(a,w)
            verify_order(b,pc,w,'v693' if a==T else 'v709')
    audit_native(src.values(),outer,expected)
    out=body
    for pc in sorted(pcs-{resume}):out=patch_callback_label(out,pc,expected[pc][1])
    s=replace_exact(src[cp],body,out)
    inc='#include "undercover/wii_callback_time_binding_v813.h"'
    if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_callback_time_v810.h','wii_callback_time_binding_v813.h')}
    files[dest/'v813_private_callback_time.h']=render(C,ts,continuation,T,roots[T],leaves)
    edits={'wii_callback_prefix_binding_v807.h':patch_prefix,'wii_si_ack_binding_v672.h':patch_ack,
           'wii_si_nested_binding_v693.h':patch_shared,'wii_si_os_leaf_binding_v709.h':patch_shared}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('callback time destination')
    for n,fn in edits.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('callback time destination')
        files[p]=fn(p.read_text())
    files[cp]=s
    for p,s in files.items():p.write_text(s)
    print(f'V813_CALLBACK_TIME_ROUTE installed=1 callback_labels={len(pcs)} shared_labels={len(expected)-len(pcs)} direct_edges=4 offset=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('callback time identity','callback time tree','callback time owner','callback time coverage','callback time overlap','callback time destination','shared time label','shared time scheduler order','callback label','callback scheduler','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V813_CALLBACK_TIME_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
