#!/usr/bin/env python3
"""Install a disabled-by-default original post-time wireless call frontier."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_callback_frontier_v820 import plan
from prepare_v667_si_dispatch import exact
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v807_callback_prefix import patch_label
from prepare_v813_callback_time import verify_order

def render(C,resume,expected,stops):
    fmt=lambda n:f'0x{n:08x}u'
    return ('#pragma once\n#include "wii_callback_frontier_v829.h"\nnamespace undercover::wii::v831 {\n'
        f'inline constexpr std::array<CallbackFrontierWord,{len(expected)}> words{{{{'+
        ','.join('CallbackFrontierWord{'+fmt(pc)+','+fmt(w)+'}' for pc,(_,w) in sorted(expected.items()))+'}};\n'
        'inline constexpr CallbackFrontierExpectation expected{'+','.join(map(fmt,(C,C+688,resume)))+
        ',words,{{'+','.join('CallbackFrontierEdge{'+fmt(pc)+','+fmt(dst)+f',{ordinal}u'+'}' for pc,(ordinal,dst) in sorted(stops.items()))+'}}};\n}\n')

def patch_prefix(s):
    a='#include "wii_callback_time_binding_v813.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_frontier_binding_v831.h"')
    a='    if(!route.start_dispatch(c,pc,w,true,si_transfer_device.held_now()))reject(1);'
    return replace_exact(s,a,a+'\n    v831::capture(c);')

def patch_time(s):
    a='#include "wii_postack_transfer_device_v771.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_frontier_binding_v831.h"')
    a='<<" continuation_executed=0 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','if(v831::enabled()){v831::start(c,pc,w,route.stage()==5);return;}std::_Exit(0);'))

def patch_ack(s):
    a='    if(v813::active())return v813::poll(c);'
    s=replace_exact(s,a,'    if(v831::active())v831::reject(3);\n'+a)
    a='if(v813::observe(a,c))return;'
    return replace_exact(s,a,'if(v831::active())v831::reject(3);'+a)

def install(dol,elf,root,host):
    q,seen,stops,A,B=plan(dol,elf)
    base,T,D,U,R,ts,leaves=q;roots,C,S,site,sb,disp=base
    original=exact(dol,elf,C,172)
    resume=ts+4
    if len(seen)!=27 or resume not in seen or len(stops)!=2 or set(dst for _,dst in stops.values())!={A,B}:
        raise ValueError('frontier geometry')
    expected={pc:(C,original[(pc-C)//4]) for pc in seen}
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('frontier tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    matches=[p for p,s in src.items() if owns_root(s,C)]
    if len(matches)!=1 or sum(entry_count(s,C) for s in src.values())!=1:raise ValueError('frontier owner')
    cp=matches[0];body=exact_function(src[cp],C)
    for pc,(_,dst) in stops.items():verify_direct(body,pc,dst)
    audit_native(src.values(),outer,expected)
    verify_order(body,resume,expected[resume][1],'v813')
    out=body
    for pc in sorted(set(seen)-{resume}):
        w=expected[pc][1]
        out=patch_label(out,pc,w).replace(f'undercover::wii::v807::before(ctx,0x{pc:08x}u,0x{w:08x}u);',f'undercover::wii::v831::before(ctx,0x{pc:08x}u,0x{w:08x}u);')
        verify_order(out,pc,w,'v831')
    s=replace_exact(src[cp],body,out)
    inc='#include "undercover/wii_callback_frontier_binding_v831.h"'
    if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_callback_frontier_v829.h','wii_callback_frontier_binding_v831.h')}
    files[dest/'v831_private_callback_frontier.h']=render(C,resume,expected,stops)
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('frontier destination')
    for n,fn in {'wii_callback_prefix_binding_v807.h':patch_prefix,'wii_callback_time_binding_v813.h':patch_time,'wii_si_ack_binding_v672.h':patch_ack}.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('frontier destination')
        files[p]=fn(p.read_text())
    files[cp]=s
    for p,s in files.items():p.write_text(s)
    print('V831_CALLBACK_FRONTIER_ROUTE installed=1 labels=27 direct_edges=2 same_tick_handoff=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('frontier geometry','frontier tree','frontier owner','frontier destination','callback label','callback scheduler','callback shared hook','shared time label','shared time scheduler order','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V831_CALLBACK_FRONTIER_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
