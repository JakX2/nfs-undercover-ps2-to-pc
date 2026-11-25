#!/usr/bin/env python3
"""Extend the authenticated second-handler fixture through original SITransfer."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import HANDLER,DISABLE,RESTORE,TIME,exact
from prepare_v668_si_ack import geometry
from prepare_owner_second_time_v966 import plan as time_plan,header as time_header
from prepare_owner_second_ack_v955 import bounded
from prepare_owner_transfer_v765 import plan as transfer_plan
from prepare_owner_second_dispatch_v946 import reachable
from prepare_owner_scheduler_v722 import ROOT,READ,rewrite
from audit_handler_third_v740 import edge
from prepare_v672_si_ack_route import call_census
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root

def plan(dol,elf):
    q,site,msr,frontier=time_plan(dol,elf)
    roots,edges,indirect,iw,hw,dw,guard,extra=q
    tr,C,D,Q,S,R,links=transfer_plan(dol,elf)
    n,*_=geometry(dol,elf);call,target,w=edge(HANDLER,exact(dol,elf,HANDLER,n),4)
    if target!=C or (D,Q)!=(DISABLE,RESTORE) or len(links)!=5 or len(tr[R])!=7:raise ValueError('transfer geometry')
    old_save=extra[0][1]
    for a in (C,S,R):
        if a in roots:
            if list(roots[a])!=list(tr[a]) or a!=old_save:raise ValueError('transfer overlap')
        else:roots[a]=list(tr[a])
    new=(*extra,(call,C,4*len(tr[C]),w,tr[C]),*((p,t,4*len(tr[t]),tr[C][(p-C)//4],tr[t]) for p,t in links))
    allow={(p,t) for p,t,_,_,_ in new}
    guard.difference_update(range(HANDLER,HANDLER+4*n,4))
    roots[HANDLER],g=bounded(HANDLER,exact(dol,elf,HANDLER,n),allow);guard.update(g)
    roots[C],g=bounded(C,tr[C],allow);guard.update(g)
    overlaps=0
    for a,ws in roots.items():
        for b,other in roots.items():
            if a>=b or b>=a+4*len(ws):continue
            if {a,b}!={old_save,S} or a+4*len(ws)!=b+4*len(other) or list(ws[(b-a)//4:])!=list(other):raise ValueError('transfer overlap')
            overlaps+=1
    if len(allow)!=13 or not 11<=len(roots)<=12:raise ValueError('transfer geometry')
    # Classify every actual original guard in the handler and its selected
    # helpers. The generated private table never leaves the owner job.
    guard_rows=[]
    for lane,root in enumerate((HANDLER,*[dst for _,dst,_,_,_ in extra[:3]],C),1):
        original=exact(dol,elf,root,len(roots[root]));census=call_census(root,original)
        for pc in sorted(guard):
            if not root<=pc<root+4*len(original):continue
            w=original[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
            ordinal,kind=census.get(pc,(0,0))
            category=kind if kind else 3 if op in (16,18) else 4 if op==19 and xo in (16,528) else 5 if op==31 and xo==146 else 6
            guard_rows.append((pc,lane,ordinal,category))
    if not guard_rows or len(guard_rows)>64:raise ValueError('guard census')
    return (roots,edges,indirect,iw,hw,dw,guard,new),site,msr,frontier,call,C,S,R,overlaps,guard_rows

def header(p,out):
    q,site,msr,frontier,call,C,S,R,overlaps,guard_rows=p
    roots,edges,indirect,iw,hw,dw,guard,extra=q
    # Keep the proven nine-root header layout, then replace its edge census.
    base=(*q[:7],extra[:7]);time_header(base,out,site,msr,frontier)
    s=out.read_text()
    old=next(l for l in s.splitlines() if ' AckEdges' in l)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    s=replace_exact(s,old,'inline constexpr std::array<std::array<uint32_t,2>,13> AckEdges{{'+','.join('std::array<uint32_t,2>{'+fmt((a,b))+'}' for a,b,_,_,_ in extra)+'}};')
    s+=f'inline constexpr uint32_t TransferCall=0x{call:08x}u,Transfer=0x{C:08x}u,TransferSave=0x{S:08x}u,TransferRestore=0x{R:08x}u;\n'
    for name,a in (('transfer_words',C),('transfer_save_words',S),('transfer_restore_words',R)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n'
    s+=f'inline constexpr unsigned TransferRootCount={len(roots)};\n'
    s+=f'inline constexpr std::array<std::array<uint32_t,4>,{len(guard_rows)}> GuardCensus{{{{'+','.join('std::array<uint32_t,4>{'+fmt(row)+'}' for row in guard_rows)+'}};\n'
    out.write_text(s)

def patch_analyzer(p,root):
    spans=sorted((a,a+4*len(ws)) for a,ws in p[0][0].items())
    a=ROOT+'\n    const auto fixture_span=[&](uint32_t pc)->bool {\n'+''.join(f'      if(func_start==0x{x:08x}u)return pc>=0x{x:08x}u&&pc<0x{y:08x}u;\n' for x,y in spans)+'      return false;\n    };\n    if(!fixture_span(func_start))continue;'
    b='        if(!fixture_span(current_pc))break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('ownership')
    f.write_text(rewrite(f.read_text(),((ROOT,a),(READ,b))))

def install(p,root):
    q,*_=p;roots,edges,indirect,_,_,_,guard,extra=q
    paths=sorted(root.glob('*.cpp'));src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    total=0;changes={}
    for a,ws in roots.items():
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1:raise ValueError('native owner')
        path=owners[0];body=exact_function(src[path],a);out=body
        expected={pc:(a,ws[(pc-a)//4]) for pc in reachable(a,ws,guard,indirect)}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('native coverage')
        for site,dst in [(lr-4,t) for t,lr,_,_ in edges]+[(s,t) for s,t,_,_,_ in extra]:
            if a<=site<a+4*len(ws):verify_direct(body,site,dst)
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            if len(pat.findall(out))!=1:raise ValueError('hook identity')
            out=pat.sub(lambda m:m[0]+f'    rfi_test::before_owned(ctx,0x{a:08x}u,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
        s=changes.get(path,src[path]);s=replace_exact(s,body,out)
        changes[path]=s;total+=len(expected)
    inc='#include "runtime/cpu_context.h"'
    for path,s in changes.items():
        s=replace_exact(s,inc,inc+'\nnamespace rfi_test {void before_owned(nwii::runtime::CPUContext&,uint32_t,uint32_t,uint32_t);}')
        path.write_text(s)
    print(f'V971_TRANSFER_NATIVE labels={total} roots={len(roots)} direct_edges={len(edges)+len(extra)} shared_suffixes={p[-2]} execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:header(q,a.output);print(f'V971_TRANSFER_GEOMETRY roots={len(q[0][0])} edges=17 shared_suffixes={q[-2]} execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('transfer geometry','transfer overlap','guard census','native owner','native coverage','hook identity','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V971_TRANSFER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
