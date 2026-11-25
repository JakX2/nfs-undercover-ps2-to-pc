#!/usr/bin/env python3
"""Compose the authenticated original dispatcher suffix, scheduler and RFI."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v667_si_dispatch import geometry,exact,DISPATCH
from prepare_owner_scheduler_v722 import plan as scheduler_plan,reachable,E,S,ROOT,READ,rewrite
from prepare_owner_context_v720 import plan as loader_plan,L,H,CALLER
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_handler_tail_v879 import plan as tail_plan
BLR=0x4e800020
def dispatcher_shape(pc,words):
    if len(words)!=4 or [direct_bl(words[i],pc+4*i) for i in (0,1,3)]!=[E,S,L]:
        raise ValueError('dispatcher epilogue calls')
    w=words[2];src=(w>>21)&31
    if w>>26!=31 or (w>>1)&1023!=444 or (w&1) or (w>>16)&31!=3 or (w>>11)&31!=src or not 14<=src<=31:
        raise ValueError('dispatcher context argument')
    return src
def plan(dol,elf):
    _,(site,_),_,_,_=geometry(dol,elf);j=site+4
    code=list(exact(dol,elf,j,4))
    reg=dispatcher_shape(j,code)
    roots,counter,hint,D,R,G,calls=scheduler_plan(dol,elf)
    loader,gqr=loader_plan(dol,elf)
    roots[H]=CALLER
    roots[j]=code+[BLR] # independent unreachable guard after original RFI call
    roots[L]=loader
    q,frame,off=tail_plan(dol,elf);tail,C,A,site,base,disp=q
    if C!=site or C in roots or A in roots:raise ValueError('tail ownership')
    roots[C]=tail[C];roots[A]=tail[A]
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in roots.items())
    if len(spans)!=10 or any(a&3 or b<=a or b-a>4096 for a,b in spans) or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):
        raise ValueError('fixture ownership')
    return roots,j,reg,gqr,counter,hint,D,R,G,calls,C,A,base,disp,frame,off
def header(p,out):
    roots,j,reg,gqr,counter,hint,D,R,G,_,C,A,base,disp,frame,off=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{name}=0x{pc:08x}u' for name,pc in zip('HJESDRGL',(H,j,E,S,D,R,G,L)))+';\n'
    s+=f'inline constexpr unsigned ContextReg={reg}u,GqrMask={gqr}u;\ninline constexpr int32_t CounterDisp={counter},HintDisp={hint};\n'
    for name,pc in zip(('resume_words','epilogue_words','enable_words','resched_words','disable_words','restore_words','guard_words','loader_words'),(H,j,E,S,D,R,G,L)):
        words=roots[pc];s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    s+=f'inline constexpr uint32_t HandlerC=0x{C:08x}u,HandlerRestore=0x{A:08x}u;\n'
    s+=f'inline constexpr unsigned HandlerFrame={frame}u,HandlerLink={off}u,HandlerBase={base}u;\ninline constexpr int32_t HandlerDisp={disp};\n'
    for name,words in (('HandlerWords',roots[C]),('HandlerTailWords',roots[C][1:]),('HandlerRestoreWords',roots[A])):
        s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    with out.open('x') as f:f.write(s)
def patch_analyzer(p,root):
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in p[0].items())
    a=ROOT+'\n    const auto fixture_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{x:08x}u&&a<0x{y:08x}u)return 0x{x:08x}u;\n' for x,y in spans
    )+'      return 0;\n    };\n    if(fixture_owner(func_start)!=func_start)continue;'
    b='        if(fixture_owner(current_pc)!=func_start)break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('fixture ownership')
    old=f.read_text();new=rewrite(old,((ROOT,a),(READ,b)))
    if new!=old:f.write_text(new)
    print('V923_OWNERSHIP roots=10 guard_isolated=1')
def install(p,root):
    roots,j,_,_,_,_,D,R,G,calls,C,A,*_=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in (range(a,a+4*len(ws),4) if a==L else reachable(a,ws))}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,edges in ((j,[(j,E),(j+4,S),(j+12,L)]),(E,calls),(C,[(C,A)])):
        owned=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(owned)!=1:raise ValueError('native call owner')
        for site,dst in edges:verify_direct(owned[0],site,dst)
    hooks={pc:w for pc,(a,w) in expected.items() if a!=G and (a!=H or pc==H)}
    seen=set();changes={}
    for p,old in sources.items():
        s=old
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V923_NATIVE_ROUTE original_dispatcher=4 original_loader=54 direct_edges=6 original_labels={sum(a not in (G,H) and pc!=j+16 for pc,(a,w) in expected.items())} fallback=0 execution=0')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:
            header(p,x.output)
            print('V923_EPILOGUE_GEOMETRY verified=1 original_dispatcher=4 scheduler_calls=2 context_call=1 context_arg=nonvolatile')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('dispatcher epilogue calls','dispatcher context argument','fixture ownership','native labels','native call owner','hook identity','hook include','hook coverage','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','helper exact root')
        print('V923_EPILOGUE_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
