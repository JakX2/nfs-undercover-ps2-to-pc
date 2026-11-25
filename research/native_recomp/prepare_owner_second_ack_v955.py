#!/usr/bin/env python3
"""Private focused second-token handler ACK; original instructions until an explicit guard."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import HANDLER,DISPATCH,exact
from prepare_v668_si_ack import geometry
from si_helper_geometry_v680 import helper_plan
from si_second_geometry_v688 import second_plan
from si_nested_geometry_v693 import nested_plan
from prepare_owner_second_dispatch_v946 import plan as dispatch_plan,reachable,patch_analyzer,header as dispatch_header
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root
from audit_handler_suffix_v728 import target
BLR=0x4e800020

def bounded(root,words,allowed):
    code=list(words);guards=set()
    for i,w in enumerate(words):
        pc=root+4*i;op=w>>26;xo=(w>>1)&1023
        bad=op==17 or op==31 and xo==146 or op==19 and (xo in (50,528) or xo==16 and w!=BLR)
        if op in (16,18):
            dst=target(pc,w)
            if w&1:bad|=(pc,dst) not in allowed or op!=18 or bool(w&2)
            else:bad|=not root<=dst<root+4*len(words)
        if bad:guards.add(pc);code[i]=BLR
    return code,guards

def plan(dol,elf):
    roots,edges,indirect,iw,hw,dw,guard=dispatch_plan(dol,elf)
    n,*_=geometry(dol,elf)
    handler=exact(dol,elf,HANDLER,n)
    first,_,_=helper_plan(dol,elf);second=second_plan(dol,elf);nested=nested_plan(dol,elf)
    extra=(first,second,nested)
    allowed={(site,dst) for site,dst,_,_,_ in extra}
    original={HANDLER:handler,**{dst:code for _,dst,_,_,code in extra}}
    if len(original)!=4 or set(original)&(set(roots)-{HANDLER}):raise ValueError('ownership')
    guard-=set((HANDLER,HANDLER+4))
    for root,ws in original.items():
        roots[root],g=bounded(root,ws,allowed);guard|=g
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=9 or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('ownership')
    return roots,edges,indirect,iw,hw,dw,guard,extra

def header(p,out):
    roots,edges,indirect,iw,hw,dw,guard,extra=p
    # V946 header renders the first six roots, plus the complete guard set.
    dispatch_header((roots,edges,indirect,iw,hw,dw,guard),out)
    fmt=lambda v:','.join(f'0x{x:08x}u' for x in v)
    with out.open('a') as f:
        for name,(_,dst,_,_,_) in zip(('Save','Completion','Nested'),extra):
            ws=roots[dst]
            f.write(f'inline constexpr uint32_t {name}=0x{dst:08x}u;\n')
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> {name.lower()}_words{{'+fmt(ws)+'};\n')
        f.write('inline constexpr std::array<std::array<uint32_t,2>,3> AckEdges{{'+','.join('std::array<uint32_t,2>{'+fmt((site,dst))+'}' for site,dst,_,_,_ in extra)+'}};\n')

def install(p,root):
    roots,edges,indirect,_,_,_,guard,extra=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws,guard,indirect)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    for site,dst in [(lr-4,a) for a,lr,_,_ in edges]+[(site,dst) for site,dst,_,_,_ in extra]:
        owner=next(a for a,ws in roots.items() if a<=site<a+4*len(ws))
        bodies=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(bodies)!=1:raise ValueError('native owner')
        verify_direct(bodies[0],site,dst)
    seen=set();changes={}
    for path,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            inc='#include "runtime/cpu_context.h"'
            if s.count(inc)!=1:raise ValueError('hook include')
            changes[path]=s.replace(inc,inc+'\n#include "rfi_test_v708.h"')
    if seen!=set(expected):raise ValueError('hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'V955_ACK_NATIVE labels={len(expected)} guarded={sum(pc in guard for pc in expected)} direct_edges={len(edges)+len(extra)} execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q[:7],a.output)
        else:header(q,a.output);print('V955_ACK_GEOMETRY roots=9 original_edges=7 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('ownership','native coverage','native owner','hook identity','hook include','hook coverage','reachability','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V955_ACK_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
