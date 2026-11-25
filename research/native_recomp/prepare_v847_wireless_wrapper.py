#!/usr/bin/env python3
"""Compose live wireless wrapper observation after the authenticated SI frontier.

Preflight only. Original code is read from the privately authenticated image.
Never install a successful return, alter SRAM, or bypass the real EXI lock.
"""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from prepare_owner_wireless_v816 import plan as wrapper_plan
from prepare_owner_callback_frontier_v820 import plan as frontier_plan
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v813_callback_time import verify_order
from prepare_v807_callback_prefix import SI
from audit_callback_frontiers_v799 import call_sites

def render(roots,order,edges,L,lw):
    hx=lambda x:f'0x{x:08x}u'
    s='#pragma once\n#include "wii_wireless_wrapper_v844.h"\nnamespace undercover::wii::v847 {\n'
    for i,a in enumerate(order):
        ws=roots[a]
        s+=f'inline constexpr std::array<uint32_t,{len(ws)}> words_{i}{{'+','.join(map(hx,ws))+'};\n'
    s+='inline constexpr WirelessExpectation expected{{{'+','.join('WirelessCode{'+hx(a)+f',words_{i}'+'}' for i,a in enumerate(order))+'}},{{'
    s+=','.join('WirelessEdge{'+','.join(map(hx,row[:3]))+f',{row[3]}u'+'}' for row in edges)
    return s+'}},'+hx(L)+','+hx(lw)+',0x806f52c0u};\n}\n'

def patch_frontier(s):
    a='#include "wii_postack_transfer_device_v771.h"'
    s=replace_exact(s,a,a+'\n#include "wii_wireless_wrapper_binding_v847.h"')
    s=replace_exact(s,'inline void finish(){','template<class C>void finish(C& c,uint32_t pc,uint32_t w){')
    a='        std::_Exit(0);'
    s=replace_exact(s,a,'        if(v847::enabled()){v847::start(c,pc,w,route.stage()==2,route.ordinal());return;}\n'+a)
    if s.count('    finish();')!=2:raise ValueError('wrapper handoff')
    return s.replace('    finish();','    finish(c,pc,w);')

def patch_ack(s):
    a='    if(v831::active())v831::reject(3);\n'
    s=replace_exact(s,a,'    if(v847::active())v847::reject(3);\n'+a)
    a='if(v831::active())v831::reject(3);if(v813::observe(a,c))return;'
    return replace_exact(s,a,'if(v847::observe(a,c))return;'+a)

def patch_leaf(s):
    a='#include "wii_callback_time_binding_v813.h"'
    s=replace_exact(s,a,a+'\n#include "wii_wireless_wrapper_binding_v847.h"')
    a='    if(v813::active()){v813::before(c,pc,word);return;}'
    return replace_exact(s,a,'    if(v847::active()){v847::before(c,pc,word);return;}\n'+a)

def patch_label(s,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    ms=list(pat.finditer(s))
    if len(ms)!=1:raise ValueError('wrapper label')
    start=ms[0].end()
    end=s.find(SI,start,start+2048)
    if end<0 or not re.fullmatch(r'(?:    ctx\.[a-z_]+_instruction_boundary\(\);\n)*',s[start:end]):
        raise ValueError('wrapper scheduler')
    end+=len(SI)
    hook=f'    undercover::wii::v847::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    if hook in s:raise ValueError('wrapper duplicate hook')
    return s[:end]+hook+s[end:]

def install(dol,elf,root,host):
    q,seen,stops,A,B=frontier_plan(dol,elf)
    C=q[0][1]
    original=exact(dol,elf,C,172)
    roots,a,b,U,L,guards=wrapper_plan(dol,elf)
    if (a,b)!=(A,B) or sorted(o for o,_ in stops.values())!=[3,5]:
        raise ValueError('wrapper frontier geometry')
    order=(A,B,U,DISABLE,RESTORE)
    if [len(roots[a]) for a in order]!=[39,30,184,5,9]:
        raise ValueError('wrapper extent')
    lw=exact(dol,elf,L,1)[0]
    edges=[(pc,original[(pc-C)//4],original[(pc+4-C)//4],o) for pc,(o,_) in sorted(stops.items())]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('wrapper tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    changes={};labels=direct=shared=0
    def owner(a):
        found=[p for p,s in src.items() if owns_root(s,a)]
        if len(found)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('wrapper owner')
        return found[0]
    def rewrite(a,rows,callee_edges,shared_leaf=False):
        nonlocal labels,direct,shared
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a)
        for site,dst in callee_edges:verify_direct(body,site,dst);direct+=1
        audit_native([body],outer,rows)
        out=body
        for pc,(_,w) in sorted(rows.items()):
            if shared_leaf:
                verify_order(body,pc,w,'v709');shared+=1
            else:
                out=patch_label(out,pc,w)
                verify_order(out,pc,w,'v847')
            labels+=1
        if out!=body:
            s=replace_exact(s,body,out)
            inc='#include "undercover/wii_wireless_wrapper_binding_v847.h"'
            if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
            changes[p]=s
    for a in order:
        rows={pc:(a,roots[a][(pc-a)//4]) for pc in reachable(a,roots[a])}
        calls=call_sites(a,roots[a])
        if any(k!=1 or dst not in roots for _,k,dst in calls):raise ValueError('wrapper call geometry')
        # The witness refuses all dependencies outside the admitted five roots
        # and EXILock before execution. Verify every original direct edge anyway.
        rewrite(a,rows,[(pc,dst) for pc,_,dst in calls],a in (DISABLE,RESTORE))
    p=owner(L);body=exact_function(src[p],L)
    audit_native([body],outer,{L:(L,lw)})
    # The trace hook stops at the lock entry, before its first label.
    rewrite(C,{pc+4:(C,original[(pc+4-C)//4]) for pc in stops},[(pc,dst) for pc,(_,dst) in stops.items()])
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_wireless_wrapper_v844.h','wii_wireless_wrapper_binding_v847.h')}
    files[dest/'v847_private_wireless_wrapper.h']=render(roots,order,edges,L,lw)
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('wrapper destination')
    for n,fn in {'wii_callback_frontier_binding_v831.h':patch_frontier,'wii_si_ack_binding_v672.h':patch_ack,'wii_si_os_leaf_binding_v709.h':patch_leaf}.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('wrapper destination')
        files[p]=fn(p.read_text())
    # Commit only after every input, hook and output path has been checked.
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V847_WIRELESS_ROUTE installed=1 labels={labels} shared_labels={shared} direct_edges={direct} lock_entry=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('wrapper frontier geometry','wrapper extent','wrapper tree','wrapper owner','wrapper call geometry','wrapper label','wrapper scheduler','wrapper duplicate hook','wrapper handoff','wrapper destination','shared time label','shared time scheduler order','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','source seam')
        print('V847_WIRELESS_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
