#!/usr/bin/env python3
"""Install an opt-in, bounded native callback prefix in a private image.

Preflight only. Original callback execution requires a separate explicit
runtime flag and a verified full-body match at the actual handler bctrl.
"""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_callback_prefix_v797 import plan
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v789_alarm_suffix import expectations
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v668_si_ack import HANDLER

SI='    ctx.si_instruction_boundary();\n'
HOOK=re.compile(r'(?m)^    undercover::wii::(?:v680::before|v768::save_before)\(ctx,[^\n]+\);\n')
LINE=re.compile(r'(?:    (?:ctx\.[a-z_]+_instruction_boundary\(\)|undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n]+\));\n)*')

def patch_label(s,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    m=list(pat.finditer(s))
    if len(m)!=1:raise ValueError('callback label')
    start=m[0].end()
    end=s.find(SI,start,start+2048)
    if end<0 or not LINE.fullmatch(s[start:end]):raise ValueError('callback scheduler')
    end+=len(SI)
    # The shared compiler save alias can already carry an earlier route
    # hook. Bypass that hook ONLY when this new exact route is active.
    post=HOOK.match(s,end)
    if post:end=post.end()
    old=s[start:end]
    hooks=list(HOOK.finditer(old))
    if len(hooks)>1:raise ValueError('callback shared hook')
    old=HOOK.sub(lambda h:'    if(!undercover::wii::v807::active()) '+h[0].lstrip(),old)
    old+=f'    undercover::wii::v807::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    return s[:start]+old+s[end:]

def patch_handler(s):
    a='#include "wii_alarm_return_binding_v786.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_prefix_binding_v807.h"')
    a='    const bool allow=v742::eligible(pc,w,ordinal,kind);'
    return replace_exact(s,a,r'''    if(v786::continue_suffix()&&v786::route.stage()==4&&
       (witness.completed_calls()&16u)&&v807::eligible(c,pc,w,ordinal,kind)){
        if(!witness.before_authenticated_indirect(c,pc,w,held(),ordinal))reject(3);
        v807::start(c,pc,w,ordinal);return;
    }
'''+a)

def patch_ack(s):
    a='    if(v786::active())return v786::poll(c);'
    s=replace_exact(s,a,'    if(v807::active())return v807::poll(c);\n'+a)
    a='if(v786::observe(a,c))return;'
    return replace_exact(s,a,'if(v807::observe(a,c))return;'+a)

def render(C,S,prefix,save):
    fmt=lambda ws:','.join(f'0x{w:08x}u' for w in ws)
    return ('#pragma once\n#include "wii_callback_prefix_v800.h"\nnamespace undercover::wii::v807 {\n'
            f'inline constexpr uint32_t callback_root=0x{C:08x}u,save_root=0x{S:08x}u;\n'
            f'inline constexpr std::array<uint32_t,{len(prefix)}> prefix{{'+fmt(prefix)+'};\n'
            f'inline constexpr std::array<uint32_t,{len(save)}> save_words{{'+fmt(save)+'};\n}\n')

def install(dol,elf,root,host):
    roots,C,S,site,_,_=plan(dol,elf)
    candidate,words,sites=expectations(dol,elf)
    prefix=roots[C][:-1];save=roots[S]
    if C!=candidate or tuple(prefix)!=words[:len(prefix)] or len(save)!=7:raise ValueError('callback geometry')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('callback tree')
    sources={p:p.read_text() for p in paths};outer=main.read_text()
    def owner(a):
        hits=[p for p,s in sources.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in sources.values())!=1:raise ValueError('callback owner')
        return hits[0]
    cp,sp,hp=map(owner,(C,S,HANDLER))
    cbody=exact_function(sources[cp],C);sbody=exact_function(sources[sp],S)
    hbody=exact_function(sources[hp],HANDLER)
    for pc in sites:verify_indirect(hbody,pc)
    verify_direct(cbody,site,S)
    expected={C+4*i:(C,w) for i,w in enumerate(prefix)}
    audit_native(sources.values(),outer,expected)
    # Exact alias body only, as compiler suffixes are deliberately shared.
    audit_native([sbody],outer,{S+4*i:(S,w) for i,w in enumerate(save)})
    changes={}
    for a,p,ws in ((C,cp,prefix),(S,sp,save)):
        s=changes.get(p,sources[p]);body=exact_function(s,a);out=body
        for i,w in enumerate(ws):out=patch_label(out,a+4*i,w)
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_callback_prefix_binding_v807.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_callback_prefix_v800.h','wii_callback_prefix_binding_v807.h','wii_callback_dispatch_device_v808.h')}
    files[dest/'v807_private_callback_prefix.h']=render(C,S,prefix,save)
    edits={'wii_si_handler_return_binding_v726.h':patch_handler,'wii_si_ack_binding_v672.h':patch_ack}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('callback destination')
    for n,fn in edits.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('callback destination')
        files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V807_CALLBACK_ROUTE installed=1 prefix_labels={len(prefix)} save_labels={len(save)} indirect_sites=2 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('callback label','callback scheduler','callback shared hook','callback geometry','callback tree','callback owner','callback destination','indirect label','indirect LR','indirect dispatch','indirect fallback','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V807_CALLBACK_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
