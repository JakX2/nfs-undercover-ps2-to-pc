#!/usr/bin/env python3
"""Install an opt-in third SI transfer observer on the full native image."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_transfer_v765 import plan
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_owner_scheduler_v722 import reachable
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v850_callback_return import BLOCK_END
from prepare_v807_callback_prefix import SI

def hook(body,pc,w,kind):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('third label')
    i=hits[0].end();stop=BLOCK_END.search(body,i);j=stop.start() if stop else len(body)
    block=body[i:j]
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or block.index('++ctx.inst_count;')>block.index(SI):
        raise ValueError('third tick')
    base=f'undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
    current='    '+base+'false);\n'
    guard='    '+base+'true);\n'
    if kind=='frontier':
        if block.count(guard)!=1 or block.index(guard)<block.index(SI):raise ValueError('third frontier')
        line=f'    if(undercover::wii::v958::third_ready && !undercover::wii::SiBinding::handoff_second_transfer(ctx,nwii::runtime::hw::pi_intsr,nwii::runtime::hw::pi_intmr,0x{pc:08x}u)) undercover::wii::v958::reject(17);\n'
        block=replace_exact(block,guard,guard+line)
    else:
        # Shared disable/restore labels already route to v958. The
        # compiler save may also have a conditional callback hook.
        hits=re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block)
        if len(hits)>1:raise ValueError('third duplicate hook')
        if hits and hits[0]==current:
            if block.index(current)<block.index(SI):raise ValueError('third tick')
        elif hits and hits[0]==guard:
            if kind!='resume':raise ValueError('third guard')
            block=replace_exact(block,guard,'    if(undercover::wii::v958::third_active()) '+current.lstrip()+'    else '+guard.lstrip())
        else:
            if hits and ('callback_active()' not in hits[0] or current.lstrip() not in hits[0]):
                raise ValueError('third shared hook')
            k=block.index(SI)+len(SI)
            block=block[:k]+'    if(undercover::wii::v958::third_active()) '+current.lstrip()+block[k:]
        # First-transfer hooks may still retain their terminal state.
        # Suppress them only while the new transfer actually owns SI.
        legacy=re.compile(r'(?m)^    ([^\n]*undercover::wii::(?:v768::(?:before|save_before|restore_before)|v680::before|v672::before)\(ctx,[^\n]+;\n)')
        block=legacy.sub(lambda m:'    if(!undercover::wii::v958::third_active()) '+m[1],block)
    return body[:i]+block+body[j:]

def install(dol,elf,root,host):
    roots,C,D,Q,S,R,edges=plan(dol,elf)
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    call,target,w=edge(HANDLER,handler,4)
    if target!=C or len(edges)!=5 or len(roots[R])!=7:raise ValueError('third geometry')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h';header=dest/'wii_third_si_transfer_v1028.h'
    if dest.is_symlink() or private.is_symlink() or not private.is_file() or header.exists() or header.is_symlink():raise ValueError('third destination')
    old=private.read_text()
    if '#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n' not in old or 'UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE' in old:
        raise ValueError('third mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):raise ValueError('third tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    def owner(addr):
        found=[x for x,t in src.items() if owns_root(t,addr)]
        if len(found)!=1 or sum(entry_count(t,addr) for t in src.values())!=1:raise ValueError('third owner')
        return found[0]
    count=0
    for addr in (HANDLER,C,S,D,Q,R):
        path=owner(addr);body=exact_function(changes.get(path,src[path]),addr);out=body
        if addr==HANDLER:
            words=handler;pcs={call,call+4};verify_direct(body,call,C)
        else:
            words=roots[addr];pcs=set(reachable(addr,words))
            if addr==C:
                for site,dst in edges:verify_direct(body,site,dst)
        expected={pc:(addr,words[(pc-addr)//4]) for pc in pcs}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('third coverage')
        for pc,(_,word) in expected.items():
            kind='frontier' if pc==call else 'resume' if pc==call+4 else 'body'
            out=hook(out,pc,word,kind)
        text=replace_exact(changes.get(path,src[path]),body,out)
        inc='#include "undercover/wii_second_ack_live_v958.h"'
        if inc not in text:text=replace_exact(text,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        if addr==HANDLER:
            for inc in ('#include "undercover/wii_si_binding_v512.h"','#include "runtime/hw/hw.h"'):
                if inc not in text:text=replace_exact(text,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[path]=text;count+=len(expected)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    spans=[(HANDLER,HANDLER+4*n,0,0),*((a,a+4*len(roots[a]),int(a==S),26 if a==R else 0) for a in (C,S,D,Q,R))]
    old=replace_exact(old,'#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n',
        '#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n#define UNDERCOVER_V1025_PRIVATE_TRANSFER 1\n#define UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE 1\n')
    old+='namespace undercover::wii::v958 {\n'
    old+='inline constexpr std::array<AckCallSpan,6> third_spans{{'+','.join('{'+fmt(row)+'}' for row in spans)+'}};\n'
    old+='inline constexpr std::array<AckCallEdge,6> third_edges{{'+','.join('{'+fmt(row)+'}' for row in [(call,C),*edges])+'}};\n}\n'
    changes[private]=old;changes[header]=(host/header.name).read_text()
    for path,text in changes.items():path.write_text(text)
    print(f'V1029_THIRD_ROUTE installed=1 native_labels={count} direct_edges=6 exclusive_device=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('third label','third tick','third frontier','third duplicate hook','third guard','third shared hook','third geometry','third destination','third mode','third tree','third owner','third coverage','source seam','native IPC coverage','native IPC label identity','native IPC label body','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V1029_THIRD_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
