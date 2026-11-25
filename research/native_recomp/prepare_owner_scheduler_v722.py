#!/usr/bin/env python3
"""Authenticate the original scheduler-enable and no-switch reschedule lane."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from apply_irq_bootstrap_v475 import rewrite
from apply_bat_roots_v586 import ROOT,READ
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_owner_leaf_v714 import bl
H=0x80004000
E=0x80529434
S=0x80529940
BLR=0x4e800020
STOP=[0x44000002,BLR]
def target(pc,w):
    op=w>>26
    if op not in (16,18):raise ValueError('branch opcode')
    bits,sign=(0xfffc,0x8000) if op==16 else (0x3fffffc,0x2000000)
    disp=((w&bits)^sign)-sign
    return disp if w&2 else pc+disp
def sda_accesses(words,op):
    return [((w&0xffff)^0x8000)-0x8000 for w in words if w>>26==op and (w>>16)&31==13]
def shapes(enable,resched,d,r):
    if len(enable)!=15 or len(resched)!=6 or enable.count(BLR)!=1 or resched.count(BLR)!=1:
        raise ValueError('scheduler extent')
    calls=[];tails=[]
    for root,words in ((E,enable),(S,resched)):
        for i,w in enumerate(words):
            pc=root+4*i;op=w>>26;xo=(w>>1)&1023
            if op in (16,18):
                dst=target(pc,w)
                if w&2:raise ValueError('absolute branch')
                if w&1:
                    if root!=E or op!=18:raise ValueError('unexpected call')
                    calls.append((pc,dst))
                elif not root<=dst<root+4*len(words):
                    if root!=S or op!=18 or dst&3:raise ValueError('external branch')
                    tails.append((pc,dst))
                elif dst<=pc:raise ValueError('unexpected loop')
            # Accept CR-tested non-linking LR returns in the reschedule leaf.
            # CTR-tested, linked, or nonzero reserved/BH forms remain refused.
            cr_return=(root==S and op==19 and xo==16 and not(w&1)
                       and ((w>>21)&30) in (4,12) and not(w&0xf800))
            if op==17 or (op==19 and (xo==528 or xo==50 or (xo==16 and w!=BLR and not cr_return))):
                if op==19:
                    print(f'V723_CONTROL_CLASS root={int(root==S)} xo={xo} bo={(w>>21)&31} link={w&1}')
                raise ValueError('unexpected control')
    if [dst for _,dst in calls]!=[d,r] or len(tails)!=1:
        raise ValueError('scheduler dependencies')
    reads=sda_accesses(enable,32);writes=sda_accesses(enable,36)
    hints=sda_accesses(resched,32)
    if len(reads)!=1 or reads!=writes or len(hints)!=1 or hints==reads or sda_accesses(resched,36):
        raise ValueError('scheduler sda geometry')
    g=tails[0][1]
    if not 0x80000000<=g<=0x817ffff8:raise ValueError('guard extent')
    return reads[0],hints[0],calls,tails[0]
def plan(dol,elf):
    sizes=parse_functions(elf)
    if sizes.get(E)!=60 or sizes.get(S)!=24:raise ValueError('symbol extent')
    e=list(exact(dol,elf,E,15));s=list(exact(dol,elf,S,6))
    d,_,r=leaf_plan(dol,elf)
    D,R=d[1],r[1]
    counter,hint,calls,tail=shapes(e,s,D,R)
    G=tail[1]
    roots={H:[bl(H,E),bl(H+4,S),0x38a50001,*STOP],E:e,S:s,D:d[5],R:r[5]}
    if not sizes.get(G):raise ValueError('tail target')
    exact(dol,elf,G,1)
    if any(a<=G<a+4*len(ws) or G<=a<G+8 for a,ws in roots.items()):
        raise ValueError('guard overlap')
    roots[G]=STOP
    return roots,counter,hint,D,R,G,calls
def header(p,out):
    roots,counter,hint,D,R,G,_=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{name}=0x{pc:08x}u' for name,pc in zip('HESDRG',(H,E,S,D,R,G)))+';\n'
    s+=f'inline constexpr int32_t CounterDisp={counter},HintDisp={hint};\n'
    for name,pc in zip(('caller','enable_words','resched_words','disable_words','restore_words','guard_words'),(H,E,S,D,R,G)):
        words=roots[pc];s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    with out.open('x') as f:f.write(s)
def reachable(root,words):
    """All statically reachable words, including both conditional paths."""
    end=root+4*len(words);seen=set();work=[root]
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:raise ValueError('reachable fallthrough')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==19 and xo==16 and ((w>>21)&20)==20 and not(w&1):continue
        if op in (16,18) and not(w&1):
            dst=target(pc,w)
            if root<=dst<end:work.append(dst)
            elif op!=18:raise ValueError('reachable external conditional')
            if op==18:continue
        work.append(pc+4)
    return seen

def ownership_pairs(roots):
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in roots.items())
    if len(spans)!=6 or any(a&3 or b<=a or b-a>4096 for a,b in spans) or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):
        raise ValueError('focused ownership')
    root=ROOT+'\n    const auto fixture_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{a:08x}u&&a<0x{b:08x}u)return 0x{a:08x}u;\n' for a,b in spans
    )+'      return 0;\n    };\n    if(fixture_owner(func_start)!=func_start)continue;'
    read='        if(fixture_owner(current_pc)!=func_start)break;\n'+READ
    return ((ROOT,root),(READ,read))

def patch_analyzer(p,root):
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('focused ownership')
    old=f.read_text();new=rewrite(old,ownership_pairs(p[0]))
    if new!=old:f.write_text(new)
    print('V724_FOCUSED_OWNERSHIP roots=6 tail_isolated=1')

def install(p,root):
    roots,_,_,D,R,G,calls=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main][sources[main].index('extern "C" void run_game('):]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    # The original ELF extent is authenticated in full. Only reachable
    # labels are required; alignment/padding after a terminal is not code.
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,edges in ((H,[(H,E),(H+4,S)]),(E,calls)):
        owned=[exact_function(s,owner) for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{owner:X}'+r'\(CPUContext& ctx\) \{',s)]
        if len(owned)!=1:raise ValueError('native call owner')
        for site,dst in edges:verify_direct(owned[0],site,dst)
    # Every original label and the independent caller are observed. The
    # external scheduler target is a refusal guard, never original code.
    hooks={pc:w for pc,(a,w) in expected.items() if a!=G}
    seen=set();changes={}
    for p,old in sources.items():
        s=old
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            matches=list(pat.finditer(s))
            if not matches:continue
            if len(matches)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V722_NATIVE_ROUTE original_labels={sum(a in (E,S,D,R) for a,w in expected.values())} direct_edges=4 guarded_tail=1 fallback=0 execution=0')
    print(f'V724_REACHABILITY labels={len(expected)} excluded={sum(map(len,roots.values()))-len(expected)}')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:
            header(p,x.output)
            print('V722_OWNER_SCHEDULER_GEOMETRY verified=1 enable=15 resched=6 leaves=14 sda_counter=1 sda_hint=1 guarded_tail=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('scheduler extent','absolute branch','unexpected call','external branch','unexpected loop','unexpected control','scheduler dependencies','scheduler sda geometry','guard extent','symbol extent','tail target','guard overlap','native labels','native call owner','hook identity','hook include','hook coverage','reachable fallthrough','reachable external conditional','focused ownership','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','helper exact root','source shape','roundtrip','ambiguous patch')
        print('V722_SCHEDULER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
