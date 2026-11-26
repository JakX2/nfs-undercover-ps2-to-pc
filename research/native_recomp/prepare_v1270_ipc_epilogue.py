#!/usr/bin/env python3
"""Extend the privately authenticated joined ACK fixture to the original RFI.

This is a non-executing geometry/fixture planner. It does not authorize
a second IRQ, service IOS, replace a scheduler branch, or model a return.
"""
import argparse,struct,re
from pathlib import Path
from prepare_v1266_joined_ack import geometry as ack_geometry,IPC,DISPATCH_RETURN
from prepare_owner_epilogue_v737 import plan as epilogue_plan
from prepare_owner_scheduler_v722 import E,S,reachable
from prepare_owner_context_v720 import L
from make_v1256_scheduler_fixture import geometry as sched_geometry,SELECT
from prepare_v667_si_dispatch import DISPATCH,DISABLE,RESTORE
from prepare_v1260_scheduler_vector import VECTOR,TRAMP,SOURCE,SC_SOURCE,VECTORS,BLR
from prepare_v419_full_start import MAX_DOL,words_at
from make_v626_ipc_fixture import assemble
from make_v624_ipc_geometry import ROOT,exact_words
from prepare_v453_debug_leaf import data_at
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from apply_bat_roots_v586 import ROOT as ANALYZE_ROOT,READ
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_irq_bootstrap_v475 import rewrite

def geometry(dol,elf):
    g,native,stop,edges,branch,ret=ack_geometry(dol,elf)
    roots,j,reg,gqr,counter,hint,d,r,switch,calls=epilogue_plan(dol,elf)
    if j!=DISPATCH_RETURN or g[2]+4!=j or g[6]&{j}==set() or roots[j][0]!=ret:
        raise ValueError('epilogue predecessor')
    if switch!=SELECT or d!=DISABLE or r!=RESTORE or counter!=g[-1]:
        raise ValueError('epilogue scheduler identity')
    if len(roots[L])!=54 or roots[L][-1]!=0x4c000064 or roots[j][-1]!=BLR:
        raise ValueError('epilogue extent')
    # Do not install the prior isolated synthetic caller or switch guard.
    # SelectThread is already a real root in the predecessor fixture.
    additions={pc:tuple(roots[pc]) for pc in (E,S,d,r,L)}
    for pc,ws in additions.items():
        if tuple(exact_words(dol,elf,pc,len(ws)))!=ws:raise ValueError('epilogue word identity')
    if any(tuple(g[0][pc])!=additions[pc] for pc in (d,r)):
        raise ValueError('epilogue shared leaf')
    return (g,native,stop,additions,j,tuple(roots[j][:4]),reg,gqr,counter,hint,d,r,switch,tuple(calls))

def merge_blocks(blocks,g,additions,j,code):
    blocks=dict(blocks)
    old=blocks.get(DISPATCH,())
    cut=(j-DISPATCH)//4
    if len(old)!=len(g[0][DISPATCH]) or len(code)!=4 or cut+4>=len(old):
        raise ValueError('dispatcher span')
    if tuple(old[:cut])!=tuple(g[0][DISPATCH][:cut]) or old[cut]!=code[0] or any(w!=BLR for w in old[cut+1:]):
        raise ValueError('dispatcher guard')
    if blocks.get(L)!=(additions[L][0],BLR):
        raise ValueError('loader predecessor')
    if SELECT not in blocks:raise ValueError('switch root')
    for pc,ws in additions.items():
        if pc!=L and pc in blocks and blocks[pc]!=tuple(ws):raise ValueError('shared epilogue span')
        blocks[pc]=tuple(ws)
    blocks[DISPATCH]=tuple(old[:cut])+tuple(code)+tuple(old[cut+4:])
    return blocks

def extend(raw,csv,p):
    g,_,_,additions,j,code,*_=p
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if name!=f'func_{pc:08X}' or not size or size%4 or pc in blocks:raise ValueError('symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    blocks=merge_blocks(blocks,g,additions,j,code)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def scope(p,sched_native,sched_stop):
    g,native,stop,additions,j,code,*_=p
    roots={pc:tuple(ws) for pc,ws in g[0].items()}
    roots.update({pc:tuple(ws) for pc,ws in sched_native.items()})
    for pc,ws in {**sched_stop,**stop}.items():roots[pc]=tuple(ws)+(BLR,)
    roots.update(native);roots.update(additions)
    # Shared Open IRQ helpers belong to the existing exact Open scope.
    roots.pop(DISABLE);roots.pop(RESTORE)
    spans=sorted([(VECTOR,152),(TRAMP,80)]+[(pc,len(ws)*4) for pc,ws in roots.items()])
    if any(n<=0 or n>4096 or pc&3 or n&3 for pc,n in spans) or any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):
        raise ValueError('epilogue ownership')
    return spans

def analyzer(s,spans):
    owner=ANALYZE_ROOT+'\n    const auto ipc_return_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+
        '      return 0;\n    };\n    if(ipc_return_owner(func_start)&&ipc_return_owner(func_start)!=func_start)continue;'
    read='        const auto ipc_return_root=ipc_return_owner(current_pc);\n        if((ipc_return_root&&ipc_return_root!=func_start)||(ipc_return_owner(func_start)&&ipc_return_root!=func_start))break;\n'+READ
    scan=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc,_ in spans)+')func.hle_hook_name.clear();'
    return rewrite(s,((ANALYZE_ROOT,owner),(READ,read),(SCANNER,scan)))

def render(p):
    _,_,_,additions,j,code,reg,gqr,counter,hint,d,r,switch,_=p
    words={j+4*i:w for i,w in enumerate(code)}
    words.update({pc+4*i:w for pc,ws in additions.items() for i,w in enumerate(ws)})
    f=lambda x:f'0x{x:08x}u'
    return ('#pragma once\n#include "wii_live_epilogue_v762.h"\n#include <array>\nnamespace v1270 {\n'
        'inline constexpr undercover::wii::LiveEpilogueExpectation expected(uint32_t context){return {'
        +','.join(map(f,(j,E,S,d,r,L,switch)))+f',context,{counter},{hint},{reg}u,{gqr}u'+'};}\n'
        'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
        +','.join('Word{'+f(a)+','+f(w)+'}' for a,w in sorted(words.items()))+'};\n}\n')

def install(root,p):
    _,_,_,additions,j,code,*rest=p
    calls=rest[-1]
    expected={j+4*i:(DISPATCH,w) for i,w in enumerate(code)}
    expected.update({pc:(a,ws[(pc-a)//4]) for a,ws in additions.items()
        for pc in (range(a,a+4*len(ws),4) if a==L else reachable(a,ws))})
    paths=sorted(root.glob('output_*.cpp'));src={p:p.read_text() for p in paths}
    if audit_native(src.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):
        raise ValueError('epilogue native coverage')
    for site,dst in ((j,E),(j+4,S),(j+12,L),*calls):
        owners=[s for s in src.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('epilogue direct owner')
        verify_direct(owners[0],site,dst)
    seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,(_,w) in expected.items():
            pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            matches=list(pattern.finditer(s))
            if not matches:continue
            if len(matches)!=1 or pc in seen:raise ValueError('epilogue hook identity')
            seen.add(pc);i=matches[0].end()
            s=s[:i]+f'    v1270_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('epilogue hook include')
            changes[p]=s.replace(anchor,anchor+'\nvoid v1270_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(expected):raise ValueError('epilogue hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V1270_EPILOGUE_TRANSLATION verified=1 native_labels={len(expected)} original_loader=54 direct_edges=5')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true');x=a.parse_args()
    try:
        if not 256<=x.dol.stat().st_size<=MAX_DOL or not 52<=x.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        dol,elf=x.dol.read_bytes(),x.elf.read_bytes();p=geometry(dol,elf)
        if x.analyzer:
            sn,ss,*_=sched_geometry(dol,elf)
            x.out.write_text(analyzer(x.out.read_text(),scope(p,sn,ss)))
            print('V1270_EPILOGUE_ANALYZER installed=1');return 0
        if x.install:install(x.out,p);return 0
        image=x.out/'fixture.dol';symbols=x.out/'symbols.csv'
        raw,csv=extend(image.read_bytes(),symbols.read_text(),p)
        with (x.out/'v1270_private_epilogue.h').open('x') as f:f.write(render(p))
        image.write_bytes(raw);symbols.write_text(csv)
        print('V1270_EPILOGUE_FIXTURE accepted=1 dispatcher_suffix=4 original_loader=54')
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1270_EPILOGUE_PREP accepted=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
