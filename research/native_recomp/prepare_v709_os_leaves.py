#!/usr/bin/env python3
"""Attach three authenticated native OS leaves only to the post-ACK route."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v625_ipc_client import audit_native,DEF,LABEL
from prepare_v574_dsp_sc import diagnostic
from prepare_v680_si_helper import verify_direct,exact_function
from audit_os_leaf_v703 import plan
from si_nested_geometry_v693 import nested_plan
def patch_nested(s):
    for a,b in (
        ('#include "v693_private_si_nested_expectations.h"','#include "v693_private_si_nested_expectations.h"\n#include "wii_si_os_leaf_binding_v709.h"'),
        ('    if(nested.stage()!=1)return false;','    if(v709::observe(a,c))return true;\n    if(nested.stage()!=1)return false;'),
        ('    if(!nested.instruction(c,pc,word,si_completion_ack_trace,true)){',
         '    v709::boundary(c,pc);\n    const bool allow=v709::eligible(pc,word,ordinal,kind);\n    if(!nested.instruction(c,pc,word,si_completion_ack_trace,true,allow)){'),
        ('    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){',
         '    if(allow){v709::start(c,pc,word);return;}\n    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){'),
        ('        if(!nested.returned(c,pc))reject();','        if(!nested.returned(c,pc))reject();\n        v709::complete();')):
        s=replace_exact(s,a,b)
    return s
def patch_poll(s):
    a='template<class C>bool poll(C& c){'
    return replace_exact(s,a,a+'\n    if(v709::active)return v709::poll(c);')
def patch_leaf(s,root,words,kind):
    fs=list(DEF.finditer(s));hits=[i for i,f in enumerate(fs) if int(f[1].split('_')[1],16)==root]
    if not hits:return s,{}
    if len(hits)!=1:raise ValueError('leaf duplicate root')
    i=hits[0];lo=fs[i].end();hi=fs[i+1].start() if i+1<len(fs) else len(s)
    body=s[lo:hi];seen={}
    for l in LABEL.finditer(body):
        pc,comment,w=(int(x,16) for x in l.groups())
        if pc in seen or pc!=comment or not root<=pc<root+4*len(words) or (pc-root)%4 or words[(pc-root)//4]!=w:raise ValueError('leaf label identity')
        seen[pc]=(root,w)
    if set(seen)!=set(range(root,root+4*len(words),4)):raise ValueError('leaf coverage')
    for pc in sorted(seen,reverse=True):
        w=seen[pc][1];pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        m=list(pat.finditer(body))
        if len(m)!=1:raise ValueError('leaf tick')
        pos=m[0].end();body=body[:pos]+f'    undercover::wii::v709::before(ctx,0x{pc:08x}u,0x{w:08x}u,{kind}u);\n'+body[pos:]
    s=s[:lo]+body+s[hi:]
    inc='#include "undercover/wii_si_os_leaf_binding_v709.h"'
    if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
    return s,seen
def render(rows):
    return '#pragma once\n#include "wii_postack_os_leaf_v703.h"\nnamespace undercover::wii::v709 {\ninline constexpr std::array<PostAckLeafExpectation,3> expected_leaves{{\n'+''.join('    {'+','.join(f'0x{x:08x}u' for x in row[:4])+f',{row[4]}u'+'},\n' for row in rows)+'}};\n}\n'
def owns_root(s,root):
    return any(int(m[1].split('_')[1],16)==root for m in DEF.finditer(s))
def entry_count(s,root):
    # The complete-image emitter can spell either fn_ or func_ and use
    # either hexadecimal case. Match exact trace target twice.
    x=f'{root:X}'
    return len(re.findall(r'(?mi)^\s*if \(nwii::runtime::g_trace_calls && ctx\.pc == 0x'+x+r'\) nwii::runtime::trace_call\(0x'+x+r', ctx\);\s*$',s))
def validate_coverage(calls,entries,seen,rows):
    counts=[entries[row[1]] for row in rows]
    wanted=sum(len(row[5]) for row in rows)
    if calls!=3 or counts!=[1,1,1] or len(seen)!=wanted:
        print(f'V713_LEAF_COVERAGE calls={calls} entry1={counts[0]} entry2={counts[1]} entry3={counts[2]} labels={len(seen)} expected={wanted}')
        raise ValueError('leaf route coverage')
def install(dol,elf,root,host):
    rows=plan(dol,elf);_,caller,_,_,_=nested_plan(dol,elf)
    shards=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('leaf tree')
    changes={};seen={};calls=0;entries={row[1]:0 for row in rows}
    for p in shards:
        old=p.read_text(encoding='utf-8');s=old
        if owns_root(s,caller):
            body=exact_function(s,caller)
            for site,target,*_ in rows:verify_direct(body,site,target);calls+=1
        for site,target,end,word,kind,code,mt in rows:
            entries[target]+=entry_count(s,target)
            s,found=patch_leaf(s,target,code,kind)
            if seen.keys()&found.keys():raise ValueError('leaf duplicate coverage')
            seen.update(found)
        if s!=old:changes[p]=s
    validate_coverage(calls,entries,seen,rows)
    if len(seen)!=20:raise ValueError('original leaf extent')
    n=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),seen)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text(encoding='utf-8') for n in ('wii_postack_os_leaf_v703.h','wii_si_os_leaf_binding_v709.h')}
    files[dest/'v709_private_os_leaf_expectations.h']=render(rows)
    bind=dest/'wii_si_nested_binding_v693.h';ack=dest/'wii_si_ack_binding_v672.h'
    if dest.is_symlink() or bind.is_symlink() or ack.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('leaf destination')
    files[bind]=patch_nested(bind.read_text(encoding='utf-8'))
    files[ack]=patch_poll(ack.read_text(encoding='utf-8'))
    for p,s in {**changes,**files}.items():p.write_text(s,encoding='utf-8')
    return n
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V709_OS_LEAF_ROUTE installed=0');return 1
    print(f'V709_OS_LEAF_ROUTE installed=1 native_labels={n} direct_edges=3 postack_only=1 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
