#!/usr/bin/env python3
"""Private expansion and native audit for original submit -> IOS_Open return."""
import argparse,struct,re
from pathlib import Path
from prepare_v1337_open_completion import (plan,merge,rebuild,ensure_resume,hook_submit,
    STM,FIRST_OPEN_CALL,OPEN,SUBMIT,BLR)
from prepare_v1281_reply_fixture import symbols
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct

def expand_scope(prior,old_size,new_size):
    out=dict(prior)
    if STM in out and out[STM]!=old_size:raise ValueError('open return ownership')
    if old_size!=96 or new_size!=136:raise ValueError('open return extent')
    out[STM]=new_size
    spans=sorted(out.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('open return ownership')
    return spans

def geometry(p):
    shared,edges,old,new,*_=p
    fr,sr,tr=edges[2][1],edges[5][1],FIRST_OPEN_CALL+4
    if len(old)!=23 or len(new)!=33 or tuple(new[:23])!=old or direct_bl(old[-1],tr-4)!=OPEN:
        raise ValueError('open return geometry')
    if not OPEN<sr<OPEN+4*len(shared[OPEN]) or not SUBMIT<fr<SUBMIT+4*len(shared[SUBMIT]):
        raise ValueError('open return geometry')
    if direct_bl(shared[OPEN][(sr-OPEN)//4-1],sr-4)!=SUBMIT:raise ValueError('open return geometry')
    return fr,sr,tr,old[-1],edges[5][2],new[23]

def render(p):
    shared,_,old,new,*_=p
    fr,sr,tr,oc,sc,tw=geometry(p)
    fmt=lambda v:f'0x{v:08x}u'
    rows=[(a,a+4*i,w) for a in (OPEN,SUBMIT) for i,w in enumerate(shared[a])]
    tail=[(STM+4*i,new[i]) for i in range(len(old),len(new))]
    return ('#pragma once\n#include "wii_open_return_v1351.h"\nnamespace v1358 {\n'
        +f'inline constexpr std::array<undercover::wii::ReplyNativeWord,{len(rows)}> words'+'{'
        +','.join('undercover::wii::ReplyNativeWord{'+','.join(map(fmt,row))+'}' for row in rows)+'};\n'
        +'inline constexpr undercover::wii::OpenReturnExpectation expected{'+','.join(map(fmt,(OPEN,SUBMIT,fr,sr,tr,oc,sc,tw)))+',words};\n'
        +'struct Word{uint32_t pc,word;};\n'+f'inline constexpr std::array<Word,{len(tail)}> stm_words'+'{'
        +','.join('Word{'+','.join(map(fmt,row))+'}' for row in tail)+'};\n}\n')

def expand(raw,csv,p):
    shared,_,old,new,*_=p
    sizes=symbols(csv)
    blocks={a:words_at(raw,a,n//4) for a,n in sizes.items()}
    expanded=merge(blocks,shared,old,new)
    image=rebuild(raw,expanded)
    rows='Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items()))
    if set(symbols(rows))!=set(sizes) or symbols(rows)[STM]!=136:raise ValueError('open return extent')
    return image,rows

def install(root,p):
    shared,_,old,new,*_=p
    fr,sr,tr,_,_,_=geometry(p)
    sources={f:f.read_text() for f in sorted(root.glob('output_*.cpp'))}
    main=(root/'main_output.cpp').read_text()
    expected={a+4*i:(a,w) for a in (OPEN,SUBMIT) for i,w in enumerate(shared[a])}
    expected.update({STM+4*i:(STM,w) for i,w in enumerate(new[:24])})
    audit_native(sources.values(),main,expected)
    for site,dst in ((sr-4,SUBMIT),(tr-4,OPEN)):
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('open return native edge')
        verify_direct(owners[0],site,dst)
    bodies=[exact_function(s,OPEN) for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{OPEN:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(bodies)!=1:raise ValueError('open return native root')
    main,added=ensure_resume(main,bodies[0],OPEN,sr)
    # All submit labels were already hooked by V1352. Only the Open
    # epilogue needs new hooks; its earlier request-building path is intact.
    wanted={pc:w for pc,(owner,w) in expected.items() if owner==OPEN and pc>=sr}
    seen=set();changes={}
    for f,s in sources.items():
        old_source=s
        for pc,w in wanted.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in seen:raise ValueError('open return duplicate hook')
            seen.add(pc)
        if s!=old_source:
            anchor='#include "runtime/cpu_context.h"'
            decl='void v1344_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);'
            if s.count(anchor)!=1 or s.count(decl)>1:raise ValueError('open return hook include')
            changes[f]=s if decl in s else s.replace(anchor,anchor+'\n'+decl)
    if seen!=set(wanted):raise ValueError('open return hook coverage')
    for f,s in changes.items():f.write_text(s)
    if added:(root/'main_output.cpp').write_text(main)
    print(f'V1358_OPEN_TRANSLATION verified=1 open_hooks={len(wanted)} native_edges=2 resume_added={int(added)} stm_original=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--analyzer',action='store_true')
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e);geometry(p)
        if q.install:install(q.out,p);return 0
        if q.analyzer:
            if q.symbols is None:raise ValueError('open return ownership')
            sizes=symbols(q.symbols.read_text())
            if sizes.get(STM)!=136:raise ValueError('open return extent')
            spans=expand_scope(combined_scope(d,e,{**sizes,STM:96}),96,136)
            q.out.write_text(analyzer(q.out.read_text(),spans))
            print('V1358_OPEN_ANALYZER verified=1 expanded_stm=1');return 0
        image=q.out/'fixture.dol';csv=q.out/'symbols.csv'
        raw,rows=expand(image.read_bytes(),csv.read_text(),p)
        with (q.out/'v1358_private_open_return.h').open('x') as f:f.write(render(p))
        image.write_bytes(raw);csv.write_text(rows)
        print('V1358_OPEN_FIXTURE verified=1 stm_original_words=33 additional_roots=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','open return ownership','open return extent','open return geometry','open return native edge',
            'open return native root','open return duplicate hook','open return hook include','open return hook coverage',
            'completion predecessor','completion shared identity','completion ownership','completion roundtrip',
            'completion local resume','completion outer resume','completion root dispatch','completion hook label',
            'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
            'helper exact root','helper call label','helper direct native call','helper native return edge')
        print('V1358_OPEN_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
