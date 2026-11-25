#!/usr/bin/env python3
"""Original OSCancelAlarm, with timer-reprogramming dependencies guarded."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge,summarize
from audit_os_leaf_v703 import plan as leaf_plan
from si_nested_geometry_v693 import nested_plan
from prepare_owner_leaf_v714 import bl
from prepare_owner_scheduler_v722 import reachable,sda_accesses,ROOT,READ,rewrite
from audit_si_deep_v695 import step as constant_step,target,signed
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
H=0x80004000
BLR=0x4e800020
# Established original SDA and queue offsets from the V47 alarm-init fixture.
SDA=0x8070e8e0
QUEUE=(SDA-3496,SDA-3492)
def queue_stores(root,words):
    end=root+4*len(words);initial=[None]*32;initial[13]=SDA
    states={root:tuple(initial)};work=[root];writes={};visits=0
    while work:
        pc=work.pop();visits+=1
        if visits>16384:raise ValueError('cancel queue analysis bound')
        w=words[(pc-root)//4];op=w>>26;rd=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023
        regs=states[pc];q=list(regs)
        if op in (36,37):
            a=regs[ra] if ra else 0
            writes[pc]=None if a is None else (a+signed(w&0xffff))&0xffffffff
        elif op==31 and xo in (151,183):
            a=regs[ra] if ra else 0;b=regs[rb]
            writes[pc]=None if a is None or b is None else (a+b)&0xffffffff
        if op==18 and w&1:
            # The independently authenticated call edges are ABI calls.
            # Do not propagate volatile register constants across them.
            for i in (0,*range(3,13)):q[i]=None
        elif op==31 and xo in (339,19,83):q[rd]=None # mfspr/mfcr/mfmsr
        elif op==31 and xo in (467,144,146,0,32):pass # mtspr/mtcrf/mtmsr/cmp
        elif op in (20,21,23):q[ra]=None # rotate/mask
        elif op==31 and xo in (266,40,10,8):
            a,b=regs[ra],regs[rb]
            q[rd]=None if a is None or b is None else ((a+b if xo in (266,10) else b-a)&0xffffffff)
        elif op==31 and xo in (28,60,124,316,536,792,824,922,954):q[ra]=None
        elif op in (7,8,12,13):q[rd]=None
        else:q=list(constant_step(w,regs)[0])
        if op==19 and xo==16 and not(w&1):continue
        if op in (16,18) and not(w&1):
            dest=[target(pc,w)]+([pc+4] if op==16 else [])
        else:dest=[pc+4]
        for a in dest:
            if a&3 or not root<=a<end:raise ValueError('cancel queue flow')
            old=states.get(a);new=tuple(q) if old is None else tuple(x if x==y else None for x,y in zip(old,q))
            if old!=new:states[a]=new;work.append(a)
    return tuple(sum(v==a for v in writes.values()) for a in QUEUE),sum(v is None for v in writes.values())
def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    C=edge(HANDLER,handler,5)[1]
    if sizes.get(C)!=280:raise ValueError('cancel extent')
    code=list(exact(dol,elf,C,70));summary,_=summarize(C,code)
    if summary['direct']!=7 or any(summary[k] for k in ('backward','indirect','tail','mtmsr','system')) or summary['returns']!=1:raise ValueError('cancel shape')
    d,_,r=leaf_plan(dol,elf);D,R=d[1],r[1];T=nested_plan(dol,elf)[1]
    edges=[(C+4*i,direct_bl(w,C+4*i)) for i,w in enumerate(code) if w>>26==18 and w&3==1]
    if len(edges)!=7 or [v for _,v in edges[:3]]!=[D,R,T] or edges[-1][1]!=R:raise ValueError('cancel dependencies')
    # Head/tail offsets were already established by the V47 alarm init.
    # Require the original cancellation code to reference both as stores.
    counts,unknown=queue_stores(C,code)
    direct=sda_accesses(code,36)
    print(f'V759_QUEUE_GEOMETRY head={counts[0]} tail={counts[1]} direct={len(direct)} unknown={unknown}')
    if not all(counts):raise ValueError('cancel queue sda')
    guards=sorted({v for _,v in edges if v not in (D,R)})
    for a in guards:
        if a!=T and sizes.get(a)!=8:raise ValueError('timer guard extent')
        exact(dol,elf,a,1)
    roots={H:[bl(H,C),0x60000000,BLR],C:code,D:d[5],R:r[5]}
    for a in guards:
        if a in roots:raise ValueError('guard overlap')
        roots[a]=[BLR]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('guard overlap')
    return roots,C,D,R,T,guards,edges
def header(p,out):
    roots,C,D,R,T,guards,_=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{a:08x}u' for k,a in zip('HCDRT',(H,C,D,R,T)))+';\n'
    s+=f'inline constexpr std::array<uint32_t,{len(guards)}> guard_roots{{'+','.join(f'0x{a:08x}u' for a in guards)+'};\n'
    for name,a in (('caller',H),('cancel_words',C),('disable_words',D),('restore_words',R)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    s+='inline constexpr std::array<uint32_t,1> guard_words{0x4e800020u};\n'
    with out.open('x') as f:f.write(s)
def patch_analyzer(p,root):
    spans=sorted((a,a+4*len(ws)) for a,ws in p[0].items())
    a=ROOT+'\n    const auto fixture_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{x:08x}u&&a<0x{y:08x}u)return 0x{x:08x}u;\n' for x,y in spans
    )+'      return 0;\n    };\n    if(fixture_owner(func_start)!=func_start)continue;'
    b='        if(fixture_owner(current_pc)!=func_start)break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('fixture ownership')
    old=f.read_text();new=rewrite(old,((ROOT,a),(READ,b)))
    if new!=old:f.write_text(new)
def install(p,root):
    roots,C,D,R,T,guards,edges=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,links in ((H,[(H,C)]),(C,edges)):
        owned=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(owned)!=1:raise ValueError('native call owner')
        for site,dst in links:verify_direct(owned[0],site,dst)
    hooks={pc:w for pc,(a,w) in expected.items() if a not in guards}
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
    print(f'V754_NATIVE_ROUTE original_labels={sum(a in (C,D,R) for a,w in expected.values())} guards={len(guards)} direct_edges=8 fallback=0 execution=0')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:
            header(p,x.output);print('V754_CANCEL_GEOMETRY verified=1 original_words=70 queue_sda=2')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('cancel extent','cancel shape','cancel dependencies','cancel queue sda','cancel queue analysis bound','cancel queue flow','timer guard extent','guard overlap','fixture ownership','native labels','native call owner','hook identity','hook include','hook coverage')
        print('V754_CANCEL_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
