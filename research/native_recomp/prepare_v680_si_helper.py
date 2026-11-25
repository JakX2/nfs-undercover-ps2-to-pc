#!/usr/bin/env python3
"""Instrument the verified first direct helper in private complete-image output."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v625_ipc_client import DEF,LABEL,audit_native
from prepare_v574_dsp_sc import diagnostic
from si_helper_geometry_v680 import helper_plan
from prepare_v668_si_ack import HANDLER
def patch_binding(s):
    for a,b in (
        ('#include "v672_private_si_ack_expectations.h"','#include "v672_private_si_ack_expectations.h"\n#include "wii_si_helper_binding_v680.h"'),
        ('    if(!si_completion_ack_trace.before(pc,word))reject(3);','    v680::handler_boundary(c,pc);\n    if(!si_completion_ack_trace.before(pc,word))reject(3);'),
        ('    if(ordinal||kind||linked){','    if(ordinal||kind||linked){\n        if(v680::start(c,pc,word,ordinal,kind))return;'),
        ('template<class C>void observe(uint32_t,C&){reject(5);}','template<class C>void observe(uint32_t a,C& c){if(v680::observe(a,c))return;reject(5);}')):
        s=replace_exact(s,a,b)
    return s
def patch_helper(s,root,words,second=False):
    fs=list(DEF.finditer(s));hits=[i for i,f in enumerate(fs) if int(f[1].split('_')[1],16)==root]
    if not hits:return s,{}
    if len(hits)!=1:raise ValueError('helper duplicate root')
    i=hits[0];lo=fs[i].end();hi=fs[i+1].start() if i+1<len(fs) else len(s)
    body=s[lo:hi];labels=list(LABEL.finditer(body))
    seen={}
    for l in labels:
        pc,comment,w=(int(x,16) for x in l.groups())
        if pc in seen or pc!=comment or pc<root or pc>=root+4*len(words) or (pc-root)%4 or words[(pc-root)//4]!=w:raise ValueError('helper label identity')
        seen[pc]=(root,w)
    if set(seen)!=set(range(root,root+4*len(words),4)):raise ValueError('helper full coverage')
    for pc in sorted(seen,reverse=True):
        w=seen[pc][1];pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        m=list(pat.finditer(body))
        if len(m)!=1:raise ValueError('helper label tick')
        pos=m[0].end()
        if second:
            from prepare_v672_si_ack_route import call_census
            ordinal,kind=call_census(root,words).get(pc,(0,0))
            line=f'    undercover::wii::v688::before(ctx,0x{pc:08x}u,0x{w:08x}u,{ordinal}u,{kind}u);\n'
        else:line=f'    undercover::wii::v680::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
        body=body[:pos]+line+body[pos:]
    s=s[:lo]+body+s[hi:]
    header='wii_si_second_binding_v688.h' if second else 'wii_si_helper_binding_v680.h'
    return replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n#include "undercover/'+header+'"'),seen
def verify_direct(s,site,target):
    m=list(re.finditer(r'(?mi)^loc_'+f'{site:X}'+r': ;\n.*?(?=^loc_[0-9a-f]+: ;|\Z)',s,re.S|re.M))
    if len(m)!=1:raise ValueError('helper call label')
    body=m[0][0]
    if len(re.findall(r'(?mi)^    ctx\.pc = 0x'+f'{target:X}'+r'; (?:fn|func)_'+f'{target:X}'+r'\(ctx\);$',body))!=1:raise ValueError('helper direct native call')
    if f'ctx.pc != 0x{site+4:X}' not in body:raise ValueError('helper native return edge')
def exact_function(s,root):
    fs=list(DEF.finditer(s));hits=[i for i,f in enumerate(fs) if int(f[1].split('_')[1],16)==root]
    if len(hits)!=1:raise ValueError('helper exact root')
    i=hits[0];return s[fs[i].start():fs[i+1].start() if i+1<len(fs) else len(s)]
def install(dol,elf,generated,host):
    (site,target,size,word,words),alias,save=helper_plan(dol,elf)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('helper tree')
    changes={};seen={};calls=entries=0;owned=None
    for p in shards:
        s=p.read_text(encoding='utf-8')
        if re.search(r'(?mi)^loc_'+f'{site:X}'+r': ;$',s):verify_direct(s,site,target);calls+=1
        entries+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);')
        new,found=patch_helper(s,target,words)
        if found:
            if seen:raise ValueError('helper duplicate root')
            seen=found;changes[p]=new;owned=exact_function(s,target)
    if calls!=1 or entries!=1 or not seen:raise ValueError('helper route coverage')
    # A compiler save suffix is deliberately shared by multiple entry roots.
    # Audit only its unique, exact function body; retain other native aliases.
    native=audit_native([owned] if alias else (p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),seen)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text(encoding='utf-8') for n in ('wii_si_first_helper_v680.h','wii_si_helper_binding_v680.h')}
    files[dest/'v680_private_si_helper_expectations.h']='#pragma once\n#include "wii_si_first_helper_v680.h"\nnamespace undercover::wii::v680 {\ninline constexpr SiHelperExpectation expected{'+','.join(f'0x{x:08x}u' for x in (site,target,target+size,word))+','+','.join(map(str,save))+'};\n}\n'
    bind=dest/'wii_si_ack_binding_v672.h'
    if dest.is_symlink() or bind.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('helper destination')
    files[bind]=patch_binding(bind.read_text(encoding='utf-8'))
    for p,s in {**changes,**files}.items():p.write_text(s,encoding='utf-8')
    return native,alias
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n,alias=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V680_SI_HELPER_ROUTE installed=0');return 1
    print(f'V680_SI_HELPER_ROUTE installed=1 native_labels={n} direct=1 nested=0 shared_alias={int(alias)} execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
