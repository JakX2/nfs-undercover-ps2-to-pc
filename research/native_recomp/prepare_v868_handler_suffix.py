#!/usr/bin/env python3
"""Authenticate original SI handler continuation after V863; no new call admitted."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from audit_handler_suffix_v728 import suffix,target
from prepare_v672_si_ack_route import call_census
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root
from prepare_v813_callback_time import verify_order
from prepare_v850_callback_return import BLOCK_END
from prepare_v807_callback_prefix import SI

def lane(root,words,start,expected):
    n,backs,stores,stops=suffix(root,words,start)
    if (n,backs,stores,tuple((k,o) for _,k,o,_ in stops))!=expected:
        raise ValueError('handler suffix census')
    end=root+4*len(words);stop={pc:(o,1 if k==1 else 2) for pc,k,o,_ in stops}
    seen={};todo=[start]
    while todo:
        pc=todo.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:raise ValueError('handler suffix extent')
        w=words[(pc-root)//4];o,k=stop.get(pc,(0,0))
        seen[pc]=(w,o,k)
        if k:continue
        op=w>>26
        if op in (16,18):
            if w&3:raise ValueError('handler suffix control')
            todo.append(target(pc,w))
            if op==18:continue
        todo.append(pc+4)
    if len(seen)!=n:raise ValueError('handler suffix coverage')
    return seen

def render(rows,status_site=0,status_write_site=0,index=None):
    h='#pragma once\n#include "wii_handler_suffix_guard_v868.h"\n#include "wii_handler_index_branch_v911.h"\nnamespace undercover::wii::v868 {\n'
    for i,items in zip((6,11),rows):
        h+=f'inline constexpr std::array<HandlerSuffixLabel,{len(items)}> after{i}{{{{'
        h+=','.join(f'HandlerSuffixLabel{{0x{pc:08x}u,0x{w:08x}u,{o}u,{k}u}}' for pc,(w,o,k) in sorted(items.items()))
        h+='}};\n'
    h+=f'inline constexpr uint32_t status_read_site=0x{status_site:08x}u;\n'
    h+=f'inline constexpr uint32_t status_write_site=0x{status_write_site:08x}u;\n'
    if index is not None:
        start,code,table,selector,dest=index
        fmt=lambda v:f'0x{v:08x}u'
        h+='inline constexpr HandlerIndexBranchExpectation index_expected{'+','.join(map(fmt,(start,*code[11:14],dest)))+',{'+','.join(map(fmt,table))+'},'+str(selector)+'u};\n'
    return h+'}\n'

def patch_return(s):
    a='inline thread_local uint32_t original_cr=0;'
    s=replace_exact(s,a,a+r'''
inline thread_local uint64_t captured_tick=0;
inline bool continue_handler(){
    const char* v=std::getenv("UNDERCOVER_V868_HANDLER_SUFFIX");
    return v&&v[0]=='1'&&v[1]=='\0';
}''')
    s=replace_exact(s,'    captured_cpu=&c;original_gp=c.gpr;original_cr=pack(c);','    captured_cpu=&c;captured_tick=c.inst_count;original_gp=c.gpr;original_cr=pack(c);')
    a='<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','if(!continue_handler())std::_Exit(0);'))

def patch_ack(s):
    if 'wii_handler_suffix_binding_v868.h' in s or 'v868::' in s:raise ValueError('handler suffix duplicate')
    a='#include "wii_si_handler_return_binding_v726.h"'
    s=replace_exact(s,a,a+'\n#include "wii_handler_suffix_binding_v868.h"')
    a='template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){'
    s=replace_exact(s,a,a+'\n    if(v868::before(c,pc,word,ordinal,kind))return;')
    a='template<class C>bool poll(C& c){'
    s=replace_exact(s,a,a+'\n    if(v868::active())return v868::poll(c);')
    a='template<class C>void observe(uint32_t a,C& c){'
    return replace_exact(s,a,a+'\n    if(v868::active())v868::reject(6);')

def verify_handler_label(body,pc,w,o,k,resume):
    prefix=(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    if resume:
        prefix+=re.escape(f'    undercover::wii::v850::dispatch_resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n')
    pat=re.compile(prefix+r'    \+\+ctx\.inst_count;\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('handler suffix label')
    start=hits[0].end();m=BLOCK_END.search(body,start);block=body[start:m.start() if m else len(body)]
    hook=f'undercover::wii::v672::before(ctx,0x{pc:08x}u,0x{w:08x}u,{o}u,{k}u);'
    rh=f'undercover::wii::v850::handler_resume(ctx,0x{pc:08x}u,0x{w:08x}u);'
    if block.count('++ctx.inst_count;') or block.count(SI)!=1 or block.count(hook)!=1 or block.index(SI)>block.index(hook):
        raise ValueError('handler suffix hook')
    if resume:
        if block.count(rh)!=1 or not block.index(SI)<block.index(rh)<block.index(hook):
            raise ValueError('handler suffix resume order')
    elif 'v850::handler_resume' in block or 'v850::dispatch_resume' in block:
        raise ValueError('handler suffix resume order')

def derive(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf)
    rows=[lane(HANDLER,words,pc+4,expect) for pc,expect in zip(sites,
        ((52,0,1,((1,7),(1,8),(1,12))),(13,1,0,((5,11),(1,12)))))]
    from audit_handler_path_v887 import unique_prefix
    if unique_prefix(rows[0],sites[0]+4)[0]!='si_status':raise ValueError('handler status identity')
    status_site=sites[0]+24
    if rows[0].get(status_site,(0,0,0))[0]>>26!=32:raise ValueError('handler status identity')
    from audit_handler_frontier_v896 import paths
    start=sites[0]+4
    if paths(rows[0],start,10)!=[('store','si_status',36)] or any(
        rows[0][start+4*i][1:]!=(0,0) or rows[0][start+4*i][0]>>26 in (16,18,19) for i in range(10)):
        raise ValueError('handler status store identity')
    status_write_site=start+36
    from prepare_owner_status_w1c_v906 import plan as branch_plan,channel_register
    from audit_handler_index_v902 import classify_index
    from prepare_owner_packet_choice_v881 import writable_spans
    branch_start,branch_code,_,_=branch_plan(dol,elf)
    candidates=classify_index(branch_code[:12]);spans=writable_spans(dol,elf)
    if branch_start!=start or len(candidates)!=1 or candidates[0][0] is not None or candidates[0][2]!=4:raise ValueError('index branch identity')
    table=candidates[0][1]
    if any(a&3 or sum(lo<=a and a+4<=hi for lo,hi in spans)!=1 for a in table):raise ValueError('index branch data')
    index=(start,branch_code,table,channel_register(branch_code),target(start+52,branch_code[13]))
    return words,sites,rows,status_site,status_write_site,index

def install(dol,elf,root,host):
    words,sites,rows,status_site,status_write_site,index=derive(dol,elf)
    merged={}
    for r in rows:
        for pc,row in r.items():
            if pc in merged and merged[pc]!=row:raise ValueError('handler suffix overlap')
            merged[pc]=row
    census=call_census(HANDLER,words)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(f.is_symlink() or not f.is_file() or f.stat().st_size>64*1024*1024 for f in paths+[main]):raise ValueError('handler suffix tree')
    owners=[]
    for f in paths:
        s=f.read_text()
        if owns_root(s,HANDLER):owners.append(exact_function(s,HANDLER))
    if len(owners)!=1:raise ValueError('handler suffix owner')
    body=owners[0]
    audit_native([body],main.read_text(),{pc:(HANDLER,w) for pc,(w,_,_) in merged.items()})
    for pc,(w,o,k) in merged.items():
        if census.get(pc,(0,0))!=(o,k):raise ValueError('handler suffix call')
        verify_order(body,pc,w,'v672')
        verify_handler_label(body,pc,w,o,k,pc in {site+4 for site in sites})
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_handler_suffix_guard_v868.h','wii_handler_suffix_binding_v868.h','wii_handler_index_branch_v911.h')}
    files[dest/'v868_private_handler_suffix.h']=render(rows,status_site,status_write_site,index)
    if dest.is_symlink() or any(f.exists() or f.is_symlink() for f in files):raise ValueError('handler suffix destination')
    for name,fn in (('wii_callback_return_binding_v850.h',patch_return),('wii_si_ack_binding_v672.h',patch_ack)):
        f=dest/name
        if f.is_symlink() or not f.is_file():raise ValueError('handler suffix destination')
        files[f]=fn(f.read_text())
    for f,s in files.items():f.write_text(s)
    print(f'V868_HANDLER_SUFFIX_ROUTE installed=1 labels={len(merged)} lane6=52 lane11=13 same_tick=1 default_disabled=1 execution=0')
    print('V890_HANDLER_STATUS_ROUTE installed=1 exact_load=1 status_only=1 execution=0')
    print('V897_HANDLER_STATUS_ROUTE installed=1 exact_store=1 w1c_only=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('index branch identity','index branch data','handler status store identity','handler status identity','handler suffix duplicate','handler suffix census','handler suffix extent','handler suffix control','handler suffix coverage','handler suffix overlap','handler suffix tree','handler suffix owner','handler suffix call','handler suffix label','handler suffix hook','handler suffix resume order','handler suffix destination','source seam','shared time label','shared time scheduler order','native IPC label identity','native IPC coverage','native IPC dispatch')
        print('V868_HANDLER_SUFFIX_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
