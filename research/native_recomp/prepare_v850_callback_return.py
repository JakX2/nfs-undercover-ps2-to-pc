#!/usr/bin/env python3
"""Privately compose the original post-setter callback return into the full image.

Only a verified unchanged setter return admits this route. Unknown indirect
targets and the changed-ID EXI transaction remain explicit stop boundaries.
"""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact
from prepare_v668_si_ack import HANDLER,geometry
from prepare_owner_callback_after_setter_v842 import plan
from prepare_v789_alarm_suffix import expectations
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v813_callback_time import verify_order
from prepare_v807_callback_prefix import SI

def render(C,resume,words,stops,R,restore,tail,callers):
    hx=lambda n:f'0x{n:08x}u'
    fmt=lambda ws:','.join(map(hx,ws))
    call=next(pc for pc,(i,k,dst) in stops.items() if i==13)
    h='#pragma once\n#include "wii_callback_suffix_v841.h"\n#include "wii_callback_return_v846.h"\nnamespace undercover::wii::v850 {\n'
    h+=f'inline constexpr std::array<CallbackSuffixWord,{len(words)}> suffix_words{{{{'+','.join('CallbackSuffixWord{'+fmt((pc,w))+'}' for pc,w in sorted(words.items()))+'}};\n'
    h+='inline constexpr CallbackSuffixExpectation suffix_expected{'+fmt((C,C+688,resume))+',suffix_words,{{'
    h+=','.join('CallbackSuffixEdge{'+fmt((pc,dst or 0))+f',{i}u'+'}' for pc,(i,k,dst) in sorted(stops.items()))+'}}};\n'
    h+='inline constexpr std::array<uint32_t,7> restore_words{'+fmt(restore)+'};\n'
    h+='inline constexpr std::array<uint32_t,4> tail_words{'+fmt(tail)+'};\n'
    h+='struct Caller{uint32_t site,word;unsigned ordinal;CallbackReturnExpectation returned;};\n'
    h+='inline constexpr std::array<Caller,2> callers{{'
    h+=','.join('Caller{'+fmt((pc,w))+f',{ordinal}u,CallbackReturnExpectation'+'{'+fmt((call,R,pc+4))+',restore_words,tail_words,'+hx(nxt)+'}}' for pc,w,ordinal,nxt in callers)
    return h+'}};\n}\n'

def patch_prefix(s):
    a='#include "wii_callback_frontier_binding_v831.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_return_binding_v850.h"')
    a='    v831::capture(c);'
    return replace_exact(s,a,a+'\n    v850::capture(c,pc,w,ordinal);')

def patch_wrapper(s):
    a='#include "wii_postack_transfer_device_v771.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_return_binding_v850.h"')
    s=replace_exact(s,'inline void finish(){','template<class C>void finish(C& c,uint32_t pc,uint32_t w){')
    a='        std::_Exit(0);'
    s=replace_exact(s,a,'        if(v850::enabled()&&route.stage()==2u&&route.ordinal()==3u&&!route.changed()){\n            v850::start(c,pc,w,true);return;\n        }\n'+a)
    s=replace_exact(s,'    finish();return true;','    finish(c,pc,0u);return true;')
    return replace_exact(s,'    finish();','    finish(c,pc,w);')

def patch_ack(s):
    a='    if(v847::active())v847::reject(3);'
    s=replace_exact(s,a,'    if(v850::active())return v850::poll(c);\n'+a)
    a='if(v847::observe(a,c))return;'
    s=replace_exact(s,a,'if(v850::observe(a,c))return;'+a)
    a='template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){'
    return replace_exact(s,a,a+'\n    if(v850::active())v850::reject(7);')

LABEL_TICK=lambda pc,w: re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
RESTORE_HOOK=re.compile(r'(?m)^    undercover::wii::(?:v768|v726)::restore_before\(ctx,[^\n]+\);\n')
INSTR_PREFIX=re.compile(r'(?:    (?:ctx\.[a-z_]+_instruction_boundary\(\)|undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n]+\));\n)*')
BLOCK_END=re.compile(r'(?mi)^loc_[0-9a-f]+: ;|^\}')

def patch_label(s,pc,w,role='before'):
    if role not in ('before','restore','handler_resume'):raise ValueError('return role')
    hits=list(LABEL_TICK(pc,w).finditer(s))
    if len(hits)!=1:raise ValueError('return label')
    m=hits[0];start=m.end()
    stop=BLOCK_END.search(s,start)
    end=stop.start() if stop else len(s)
    block=s[start:end]
    if block.count(SI)!=1:raise ValueError('return scheduler')
    pos=block.index(SI)
    if not INSTR_PREFIX.fullmatch(block[:pos]):raise ValueError('return scheduler')
    if 'undercover::wii::v850::' in block:raise ValueError('return duplicate hook')
    old=list(RESTORE_HOOK.finditer(block))
    if role=='restore':
        if len(old)>1:raise ValueError('return shared hook')
        block=RESTORE_HOOK.sub(lambda h:'    if(!undercover::wii::v850::active()) '+h[0].lstrip(),block)
    elif old:raise ValueError('return shared hook')
    if role=='handler_resume':
        hook='    undercover::wii::v672::before(ctx,'
        if block.count(hook)!=1 or block.index(hook)<block.index(SI):raise ValueError('return handler hook')
    after=block.index(SI)+len(SI)
    name='handler_resume' if role=='handler_resume' else 'before'
    block=block[:after]+f'    undercover::wii::v850::{name}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+block[after:]
    prefix=s[:start]
    if role=='handler_resume':
        a='    ++ctx.inst_count;\n'
        if not prefix.endswith(a):raise ValueError('return tick')
        prefix=prefix[:-len(a)]+f'    undercover::wii::v850::dispatch_resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+a
    return prefix+block+s[end:]

def install(dol,elf,root,host):
    joined,C,resume,seen,stops=plan(dol,elf,True)
    roots=joined[1][0][0]
    code=exact(dol,elf,C,172)
    call,R=next((pc,dst) for pc,(i,k,dst) in stops.items() if i==13)
    restore=roots[R];tail=code[(call+4-C)//4:(call+20-C)//4]
    if len(restore)!=7 or len(tail)!=4 or resume not in seen:raise ValueError('return geometry')
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    candidate,_,sites=expectations(dol,elf)
    if candidate!=C or len(sites)!=2:raise ValueError('return caller')
    callers=[(pc,handler[(pc-HANDLER)//4],i,handler[(pc+4-HANDLER)//4]) for pc,i in zip(sites,(6,11))]
    if any(w!=0x4e800421 for _,w,_,_ in callers):raise ValueError('return caller')
    suffix_words={pc:code[(pc-C)//4] for pc in seen}
    tails={call+4+4*i:w for i,w in enumerate(tail)}
    if set(tails)&set(suffix_words):raise ValueError('return overlap')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('return tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    def owner(a):
        found=[p for p,s in src.items() if owns_root(s,a)]
        if len(found)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('return owner')
        return found[0]
    def edit(a,fn):
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a)
        out=fn(body)
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_callback_return_binding_v850.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    def callback(body):
        expected={pc:(C,w) for pc,w in {**suffix_words,**tails}.items()}
        audit_native([body],outer,expected)
        for pc,(i,k,dst) in stops.items():
            if k==1:verify_direct(body,pc,dst)
            elif k==2:verify_indirect(body,pc)
            else:raise ValueError('return edge')
        # V847's wrapper has already observed this same tick.
        verify_order(body,resume,suffix_words[resume],'v847')
        out=body
        for pc,(_,w) in sorted(expected.items()):
            if pc==resume:continue
            out=patch_label(out,pc,w)
            verify_order(out,pc,w,'v850')
        return out
    def alias(body):
        rows={R+4*i:(R,w) for i,w in enumerate(restore)}
        audit_native([body],outer,rows)
        out=body
        for pc,(_,w) in rows.items():
            out=patch_label(out,pc,w,'restore')
            verify_order(out,pc,w,'v850')
        return out
    def handler_resume(body):
        rows={pc:(HANDLER,w) for pc,w,_,_ in callers}
        rows.update({pc+4:(HANDLER,nxt) for pc,_,_,nxt in callers})
        audit_native([body],outer,rows)
        out=body
        for pc,w,ordinal,nxt in callers:
            verify_indirect(body,pc)
            verify_resume_dispatch(outer,HANDLER,pc+4)
            verify_order(body,pc+4,nxt,'v672')
            out=patch_label(out,pc+4,nxt,'handler_resume')
        return out
    edit(C,callback);edit(R,alias);edit(HANDLER,handler_resume)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_callback_suffix_v841.h','wii_callback_return_v846.h','wii_callback_return_binding_v850.h')}
    files[dest/'v850_private_callback_return.h']=render(C,resume,suffix_words,stops,R,restore,tail,callers)
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('return destination')
    for n,fn in {'wii_callback_prefix_binding_v807.h':patch_prefix,'wii_wireless_wrapper_binding_v847.h':patch_wrapper,'wii_si_ack_binding_v672.h':patch_ack}.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('return destination')
        files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print('V850_CALLBACK_RETURN_ROUTE installed=1 suffix_labels=21 restore_labels=7 tail_labels=4 handler_resumes=2 outer_tick=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('return role','return label','return scheduler','return duplicate hook','return shared hook','return handler hook','return tick','return geometry','return caller','return overlap','return tree','return owner','return edge','return destination','source seam','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','resume dispatcher identity','shared time label','shared time scheduler order','indirect label','indirect LR','indirect dispatch','indirect fallback')
        print('V850_CALLBACK_RETURN_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
