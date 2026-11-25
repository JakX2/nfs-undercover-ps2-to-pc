#!/usr/bin/env python3
"""Compose V879's authenticated original handler return after V868. Opt-in."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v668_si_ack import HANDLER
from prepare_v667_si_dispatch import DISPATCH,geometry,exact
from prepare_owner_handler_tail_v879 import plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v850_callback_return import LABEL_TICK,BLOCK_END
from prepare_v807_callback_prefix import SI

def render(dol,elf):
    q,_,_=plan(dol,elf);roots,C,S,_,_,_=q
    _,(site,_),_,_,_=geometry(dol,elf)
    resume=site+4;w=exact(dol,elf,resume,1)[0]
    fmt=lambda ws:','.join(f'0x{x:08x}u' for x in ws)
    h='#pragma once\n#include "wii_callback_return_v846.h"\nnamespace undercover::wii::v884 {\n'
    h+='inline constexpr HandlerReturnExpectation expected{'+fmt((C,S,resume))+',{'+fmt(roots[S])+'},{'+fmt(roots[C][1:])+'},'+fmt((w,))+'};\n}\n'
    return C,S,roots[C],roots[S],resume,w,h

def patch_suffix(s):
    if 'v884::' in s:raise ValueError('handler tail duplicate')
    a='#include "wii_callback_return_binding_v850.h"'
    s=replace_exact(s,a,a+'\n#include "wii_handler_tail_binding_v884.h"')
    a='    if(!v850::continue_handler()||'
    s=replace_exact(s,a,'    if(v884::active()){v884::handler_before(c,pc,w,ordinal,kind);return true;}\n'+a)
    a='    if(kind){'
    s=replace_exact(s,a,a+'\n        if(v884::start(c,pc,w,ordinal,kind))return true;')
    a='template<class C>bool poll(C& c){'
    return replace_exact(s,a,a+'\n    if(v884::active())return v884::poll(c);')

def patch_ack(s):
    a='    if(v868::active())v868::reject(6);'
    return replace_exact(s,a,'    if(v884::active()){v884::observe(a,c);return;}\n'+a)

def patch_label(body,pc,w,role):
    hits=list(LABEL_TICK(pc,w).finditer(body))
    if len(hits)!=1:raise ValueError('handler tail label')
    start=hits[0].end();m=BLOCK_END.search(body,start);end=m.start() if m else len(body)
    block=body[start:end];prefix=body[:start]
    if block.count(SI)!=1 or 'v884::' in block:raise ValueError('handler tail scheduler')
    prefix_hooks=block[:block.index(SI)]
    # Only existing observer hooks may precede the real SI instruction
    # service. Do not move it across an emitted guest state mutation.
    allowed=re.compile(r'(?:    (?:ctx\.[a-z_]+_instruction_boundary\(\)|undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n;]+\)|if\((?:!undercover::wii::v[0-9]+::active\(\)(?:&&)?)+\) (?:\{ )?undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n;]+\));(?: \})?\n)*')
    if not allowed.fullmatch(prefix_hooks):raise ValueError('handler tail scheduler')
    if role=='alias':
        old=re.compile(r'(?m)^    (?:if\([^\n]+\) )?(?:\{ )?undercover::wii::v726::restore_before\(ctx,[^\n]+\);(?: \})?\n')
        hooks=list(old.finditer(block))
        if len(hooks)>1:raise ValueError('handler tail legacy')
        if hooks:
            a=hooks[0][0]
            if a.lstrip().startswith('if('):
                block=replace_exact(block,a,'    if(!undercover::wii::v884::active()) { '+a.strip()+' }\n')
            else:block=replace_exact(block,a,'    if(!undercover::wii::v884::active()) '+a.lstrip())
        call=f'    undercover::wii::v884::before_alias(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    elif role=='resume':
        a=f'    undercover::wii::v726::resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
        block=replace_exact(block,a,'    if(!undercover::wii::v884::active()) '+a.lstrip())
        tick='    ++ctx.inst_count;\n'
        if not prefix.endswith(tick):raise ValueError('handler tail tick')
        prefix=prefix[:-len(tick)]+f'    undercover::wii::v884::dispatch_resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+tick
        call=f'    undercover::wii::v884::resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    else:raise ValueError('handler tail role')
    after=block.index(SI)+len(SI)
    return prefix+block[:after]+call+block[after:]+body[end:]

def install(dol,elf,root,host):
    C,S,tail,restore,resume,w,header=render(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('handler tail tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('handler tail owner')
        return hits[0]
    h=exact_function(src[owner(HANDLER)],HANDLER)
    verify_direct(h,C,S);verify_resume_dispatch(outer,DISPATCH,resume)
    audit_native([h],outer,{C+4*i:(HANDLER,x) for i,x in enumerate(tail)})
    for i,x in enumerate(tail):
        from prepare_v813_callback_time import verify_order
        verify_order(h,C+4*i,x,'v672')
    for a,rows,role in ((S,[(S+4*i,x) for i,x in enumerate(restore)],'alias'),(DISPATCH,[(resume,w)],'resume')):
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        audit_native([body],outer,{pc:(a,x) for pc,x in rows})
        for pc,x in rows:out=patch_label(out,pc,x,role)
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_handler_tail_binding_v884.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/'wii_handler_tail_binding_v884.h':(host/'wii_handler_tail_binding_v884.h').read_text(),dest/'v884_private_handler_tail.h':header}
    if dest.is_symlink() or any(f.exists() or f.is_symlink() for f in files):raise ValueError('handler tail destination')
    for name,fn in (('wii_handler_suffix_binding_v868.h',patch_suffix),('wii_si_ack_binding_v672.h',patch_ack)):
        p=dest/name
        if p.is_symlink() or not p.is_file():raise ValueError('handler tail destination')
        files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print('V884_HANDLER_TAIL_ROUTE installed=1 restore_labels=16 tail_labels=4 dispatcher_resume=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('handler tail duplicate','handler tail label','handler tail scheduler','handler tail legacy','handler tail tick','handler tail role','handler tail tree','handler tail owner','handler tail destination','source seam','resume dispatcher identity','shared time label','shared time scheduler order','native IPC label identity','native IPC coverage','native IPC dispatch')
        print('V884_HANDLER_TAIL_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
