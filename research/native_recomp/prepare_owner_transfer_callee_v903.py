#!/usr/bin/env python3
"""Compose authentic nested GPR-save aliases with selected original SITransfer lanes."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_callee_v895 import plan as old_plan,header as old_header
from prepare_owner_callee_save_v899 import plan as nested_plan
from prepare_owner_scheduler_v722 import reachable,ROOT,READ,rewrite
from prepare_v625_ipc_client import DEF,audit_native
from prepare_v680_si_helper import verify_direct
from classify_save_leaf_v683 import classify_suffix
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import names
from prepare_v419_full_start import direct_bl

def validate_roots(roots,aliases):
    # Overlap is legal only for independently authenticated compiler-save
    # suffixes with byte-identical overlap and the same original end.
    for a,ws in roots.items():
        if a&3 or not ws:raise ValueError('shared root extent')
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    shared=0
    for i,(a,b) in enumerate(spans):
        for c,d in spans[i+1:]:
            if c>=b:break
            if a not in aliases or c not in aliases or b!=d or roots[a][(c-a)//4:]!=roots[c]:
                raise ValueError('shared root overlap')
            if any(classify_suffix(roots[x])['kind']!=1 for x in (a,c)):
                raise ValueError('shared root kind')
            shared+=1
    return shared

def plan(dol,elf):
    q=old_plan(dol,elf);roots,C,S,*_=q[0][0][0]
    nested=[]
    for lane in (5,6):
        local,addr,save,site,_,_=nested_plan(dol,elf,lane)
        if addr!=q[-1][lane-5][1] or save in roots:raise ValueError('nested root identity')
        roots[addr]=local[addr];roots[save]=local[save]
        nested.append((addr,save,site))
    sizes=parse_functions(elf);stops=[]
    for addr,save,site in nested:
        n=sizes.get(addr,0)
        if not 4<n<=4096 or n%4:raise ValueError('continuation extent')
        code=list(exact(dol,elf,addr,n//4))
        start=(site-addr)//4+1
        if code[:start+1]!=roots[addr][:-1]:raise ValueError('continuation identity')
        for i in range(start,min(start+32,len(code))):
            w=code[i];op=w>>26;xo=(w>>1)&1023
            if op in (16,17,18,19) or (op==31 and xo==146):
                if i==start:raise ValueError('continuation empty')
                roots[addr]=code[:i]+[0x4e800020]
                label=names(elf,direct_bl(w,addr+4*i)) if op==18 and w&3==1 else 'local_or_system'
                stops.append((addr+4*i,w,label,i-start))
                break
        else:raise ValueError('continuation bound')
    shared=validate_roots(roots,{S,*(x[1] for x in nested)})
    return q,nested,shared,stops

def header(p,out):
    q,nested,shared,stops=p;roots=q[0][0][0][0]
    # V895 header reads selected callee words from its descriptor; replace
    # those descriptors with the longer original prefix, keeping its stop
    # metadata private. The new witness stops at the original resume.
    old_header(q,out)
    f=lambda w:f'0x{w:08x}u'
    with out.open('a') as h:
        for name,(addr,save,site),(stop,w,label,count) in zip(('Alarm','Immediate'),nested,stops):
            h.write(f'inline constexpr uint32_t {name}Save={f(save)},{name}SaveSite={f(site)},{name}Resume={f(site+4)};\n')
            h.write(f'inline constexpr uint32_t {name}NextStop={f(stop)},{name}NextControl={f(w)};\n'.replace('\n','\\n'))
            for suffix,words in (('Full',roots[addr]),('SaveWords',roots[save])):
                h.write(f'inline constexpr std::array<uint32_t,{len(words)}> {name}{suffix}{{'+','.join(map(f,words))+'};\n')
    for ordinal,(_,w,label,count) in zip((5,6),stops):
        print(f'V903_CALLEE_CONTINUATION ordinal={ordinal} words={count} next_opcode={w>>26} next_name={label} execution=0')
    print(f'V903_NESTED_GEOMETRY verified=1 aliases=3 shared_pairs={shared} execution=0')

def patch_analyzer(roots,root):
    rows=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    a=ROOT+'\n    const auto fixture_contains=[](uint32_t owner,uint32_t a)->bool {\n'+''.join(
        f'      if(owner==0x{x:08x}u)return a>=0x{x:08x}u&&a<0x{y:08x}u;\n' for x,y in rows
    )+'      return false;\n    };\n    if(!fixture_contains(func_start,func_start))continue;'
    b='        if(!fixture_contains(func_start,current_pc))break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('fixture ownership')
    old=f.read_text();new=rewrite(old,((ROOT,a),(READ,b)))
    if new!=old:f.write_text(new)

def install(p,root):
    q,nested,_,_=p;roots,C,S,site,*_=q[0][0][0]
    paths=sorted(root.glob('*.cpp'))
    if not paths or any(x.is_symlink() or x.stat().st_size>4*1024*1024 for x in paths):raise ValueError('native tree')
    src={x:x.read_text() for x in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    H=next(iter(roots));links={H:[(H,C)],C:[(site,S),*q[0][3][1:]],q[2]:[(l[0],l[1]) for l in q[6]]}
    for addr,save,site in nested:links[addr]=[(site,save)]
    seen=set();labels=0;changes={}
    for path,old in src.items():
        fs=list(DEF.finditer(old));new=old
        for i in reversed(range(len(fs))):
            f=fs[i];owner=int(f[1].split('_')[1],16)
            if owner not in roots or owner in seen:raise ValueError('native root ownership')
            end=fs[i+1].start() if i+1<len(fs) else len(old);body=old[f.start():end]
            expected={pc:(owner,roots[owner][(pc-owner)//4]) for pc in reachable(owner,roots[owner])}
            if audit_native([body],outer,expected)!=len(expected):raise ValueError('native root coverage')
            for pc,dst in links.get(owner,()):verify_direct(body,pc,dst)
            for pc,(_,word) in expected.items():
                pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {word:08X}'+r'\n    \+\+ctx\.inst_count;\n')
                matches=list(pat.finditer(body))
                if len(matches)!=1:raise ValueError('native root hook')
                body=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{word:08x}u);\n',body,count=1)
            new=new[:f.start()]+body+new[end:]
            seen.add(owner);labels+=len(expected)
        if new!=old:
            anchor='#include "runtime/cpu_context.h"'
            if new.count(anchor)!=1:raise ValueError('native root include')
            changes[path]=new.replace(anchor,anchor+'\n#include "rfi_test_v708.h"')
    if seen!=set(roots):raise ValueError('native root coverage')
    for path,new in changes.items():path.write_text(new)
    print(f'V903_NESTED_NATIVE_ROUTE roots={len(seen)} owner_labels={labels} shared_alias=1 fallback=0 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q[0][0][0][0][0],a.output)
        else:header(q,a.output)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('continuation extent','continuation identity','continuation empty','continuation bound','nested root identity','shared root extent','shared root overlap','shared root kind','fixture ownership','native tree','native root ownership','native root coverage','native root hook','native root include','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge','helper call label')
        print('V903_NESTED_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
