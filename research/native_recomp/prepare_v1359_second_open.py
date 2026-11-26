#!/usr/bin/env python3
"""Install private second STM Open corridor on the authenticated V1358 image."""
import argparse,struct
from pathlib import Path
from prepare_v1337_open_completion import plan,STM,SECOND,OPEN,FIRST_OPEN_CALL,hook_submit,ensure_resume
from prepare_v629_stm_open import geometry as stm_geometry
from prepare_v419_full_start import MAX_DOL
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct

def install(root,p,paths):
    shared,edges,old,new,visits,exits,*_=p
    resume=FIRST_OPEN_CALL+4
    if len(visits)!=10 or len(exits)!=1 or visits[0]!=resume or visits[-1]!=SECOND:
        raise ValueError('second corridor')
    expected={pc:(STM,new[(pc-STM)//4]) for pc in visits}
    sources={f:f.read_text() for f in sorted(root.glob('output_*.cpp'))}
    main=(root/'main_output.cpp').read_text()
    audit_native(sources.values(),main,expected)
    owners=[s for s in sources.values() if f'loc_{SECOND:X}: ;' in s]
    if len(owners)!=1:raise ValueError('second call owner')
    verify_direct(owners[0],SECOND,OPEN)
    main,added=ensure_resume(main,exact_function(owners[0],STM),STM,resume)
    seen=set();changes={}
    for f,s in sources.items():
        prev=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in seen:raise ValueError('second duplicate hook')
            seen.add(pc)
        if s!=prev:
            anchor='#include "runtime/cpu_context.h"'
            decl='void v1344_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);'
            if s.count(anchor)!=1 or s.count(decl)>1:raise ValueError('second hook include')
            changes[f]=s if decl in s else s.replace(anchor,anchor+'\n'+decl)
    if seen!=set(expected):raise ValueError('second hook coverage')
    fmt=lambda v:f'0x{v:08x}u'
    rows=[(STM,pc,w) for pc,(_,w) in expected.items()]
    h=('#pragma once\n#include "wii_stm_second_v1359.h"\nnamespace v1359 {\n'
       +f'inline constexpr std::array<undercover::wii::ReplyNativeWord,{len(rows)}> words'+'{'
       +','.join('undercover::wii::ReplyNativeWord{'+','.join(map(fmt,row))+'}' for row in rows)+'};\n'
       +f'inline constexpr std::array<uint32_t,{len(exits)}> exits'+'{'+','.join(map(fmt,exits))+'};\n'
       +f'inline constexpr std::array<undercover::wii::StmPath,{len(paths)}> paths'+'{'
       +','.join('undercover::wii::StmPath{'+','.join(map(fmt,row))+'}' for row in paths)+'};\n'
       +'inline constexpr undercover::wii::StmSecondExpectation expected{'+','.join(map(fmt,(resume,SECOND,OPEN,shared[OPEN][0])))+',words,exits,paths};\n}\n')
    with (root.parent/'input'/'v1359_private_second.h').open('x') as f:f.write(h)
    for f,s in changes.items():f.write_text(s)
    if added:(root/'main_output.cpp').write_text(main)
    print(f'V1359_SECOND_TRANSLATION verified=1 labels={len(rows)} direct_edge=1 resume_added={int(added)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('generated',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        install(q.generated,plan(d,e),stm_geometry(d,e)[4])
        return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('second corridor','second call owner','second duplicate hook','second hook include','second hook coverage',
            'completion local resume','completion outer resume','completion root dispatch','completion hook label',
            'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
            'helper exact root','helper call label','helper direct native call','helper native return edge')
        print('V1359_SECOND_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
