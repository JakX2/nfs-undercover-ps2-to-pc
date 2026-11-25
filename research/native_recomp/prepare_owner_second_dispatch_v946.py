#!/usr/bin/env python3
"""Private focused second IRQ dispatcher: original prefix, original direct leaves, handler boundary."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import geometry,exact,DISPATCH,HANDLER,SCHED,TIME,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
from prepare_owner_scheduler_v722 import ROOT,READ,rewrite
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root
from audit_handler_suffix_v728 import target
BLR=0x4e800020
SC=0x44000002
def plan(dol,elf):
    edges,(indirect,iw),hw,dw,_=geometry(dol,elf)
    sizes=parse_functions(elf)
    roots={a:list(exact(dol,elf,a,sizes[a]//4)) for a in (DISPATCH,SCHED,TIME,DISABLE,RESTORE)}
    # Preserve all original words through the selected indirect dispatch;
    # every later dispatcher label is a deliberate refusal guard.
    cut=(indirect-DISPATCH)//4+1
    roots[DISPATCH][cut:]=[BLR]* (len(roots[DISPATCH])-cut)
    roots[HANDLER]=[hw,BLR]
    allowed={(lr-4,a) for a,lr,_,_ in edges}
    guard=set()
    for root,words in tuple(roots.items()):
        if root==HANDLER:continue
        for i,w in enumerate(words):
            pc=root+4*i;op=w>>26;xo=(w>>1)&1023
            if root==DISPATCH and i>=cut:guard.add(pc);continue
            if op in (16,18):
                dst=target(pc,w)
                if w&1:
                    if (pc,dst) not in allowed:guard.add(pc);words[i]=BLR
                elif not root<=dst<root+4*len(words):
                    guard.add(pc);words[i]=BLR
            if op==17 or op==19 and xo==50 or op==19 and xo==528 and pc!=indirect:
                guard.add(pc);words[i]=BLR
    # Exact original handler entry is not executed: the native trace stops first.
    guard.update((HANDLER,HANDLER+4))
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('ownership')
    return roots,edges,indirect,iw,hw,dw,guard
def reachable(root,words,guard,indirect):
    seen=set();work=[root];end=root+4*len(words)
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:raise ValueError('reachability')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if pc in guard or pc==indirect or op==19 and xo==16 and ((w>>21)&20)==20 and not(w&1):continue
        if op in (16,18) and not(w&1):
            work.append(target(pc,w))
            if op==18:continue
        work.append(pc+4)
    return seen
def header(p,out):
    roots,edges,indirect,iw,hw,dw,guard=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n#include "wii_si_dispatch_v667.h"\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{a:08x}u' for k,a in zip(('Dispatcher','Scheduler','Time','Disable','Restore','Handler'),roots))+';\n'
    for name,(a,ws) in zip(('dispatcher_words','scheduler_words','time_words','disable_words','restore_words','handler_words'),roots.items()):
        s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    fmt=lambda vs:','.join(f'0x{v:08x}u' for v in vs)
    s+='inline constexpr undercover::wii::SiDispatchExpectations DispatchExpected{{'+','.join('undercover::wii::SiDispatchEdge{'+fmt(x)+'}' for x in edges)+'},'+fmt((indirect,iw,hw,dw))+'};\n'
    s+=f'inline constexpr std::array<uint32_t,{len(guard)}> Guard{{'+fmt(sorted(guard))+'};\n'
    with out.open('x') as f:f.write(s)
def patch_analyzer(p,root):
    spans=sorted((a,a+4*len(ws)) for a,ws in p[0].items())
    a=ROOT+'\n    const auto fixture_owner=[](uint32_t a)->uint32_t {\n'+''.join(f'      if(a>=0x{x:08x}u&&a<0x{y:08x}u)return 0x{x:08x}u;\n' for x,y in spans)+'      return 0;\n    };\n    if(fixture_owner(func_start)!=func_start)continue;'
    b='        if(fixture_owner(current_pc)!=func_start)break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('ownership')
    f.write_text(rewrite(f.read_text(),((ROOT,a),(READ,b))))
def install(p,root):
    roots,edges,indirect,iw,hw,dw,guard=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws,guard,indirect)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    for a,lr,_,_ in edges:
        site=lr-4;owner=DISPATCH if site<SCHED else SCHED
        found=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(found)!=1:raise ValueError('native owner')
        verify_direct(found[0],site,a)
    hooks={pc:w for pc,(a,w) in expected.items() if a!=HANDLER}
    seen=set()
    for p,s in sources.items():
        old=s
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            p.write_text(s.replace(a,a+'\n#include "rfi_test_v708.h"'))
    if seen!=set(hooks):raise ValueError('hook coverage')
    print(f'V946_DISPATCH_NATIVE labels={len(expected)} original_labels={sum(pc not in guard for pc in expected)} direct_edges=4 indirect=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:
            header(q,a.output);print(f'V946_DISPATCH_GEOMETRY roots=6 original_edges=4 guarded_labels={len(q[-1])} execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('ownership','reachability','native coverage','native owner','hook identity','hook include','hook coverage','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V946_DISPATCH_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
