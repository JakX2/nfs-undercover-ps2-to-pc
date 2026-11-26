#!/usr/bin/env python3
"""Authenticate the active STM interrupt's exact native post-mtmsr resume label."""
import argparse
import re
import struct
from pathlib import Path
from prepare_stm_outer_restore import plan,RESTORE
from prepare_v1270_ipc_epilogue import geometry as epilogue_geometry
from prepare_v1337_open_completion import ensure_resume
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v419_full_start import MAX_DOL

def derive(d,e):
    caller,caller_word,enable,resume,resume_word,words=plan(d,e)
    _,_,_,additions,j,code,*_=epilogue_geometry(d,e)
    if resume!=enable+4 or resume not in words or words[resume]!=(RESTORE,resume_word):
        raise ValueError('active resume identity')
    ws=additions[RESTORE]
    if any(not RESTORE<=pc<RESTORE+4*len(ws) or owner!=RESTORE or ws[(pc-RESTORE)//4]!=w
           for pc,(owner,w) in words.items()):raise ValueError('active shared restore')
    if not code or len(code)!=4:raise ValueError('active dispatcher suffix')
    return resume,resume_word,words

def install(root,p):
    resume,word,words=p
    main=root/'main_output.cpp'
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,main.read_text(),words)
    bodies=[exact_function(s,RESTORE) for s in sources if re.search(r'(?mi)^void (?:fn|func)_'+f'{RESTORE:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(bodies)!=1:raise ValueError('active resume owner')
    hook=f'    v1270_before(ctx,0x{resume:08x}u,0x{word:08x}u);'
    if sum(s.count(hook) for s in sources)!=1:raise ValueError('active resume hook')
    out,added=ensure_resume(main.read_text(),bodies[0],RESTORE,resume)
    if added:main.write_text(out)
    print(f'DEFERRED_ACTIVE_RESUME_TRANSLATION verified=1 labels={len(words)} local_resume=1 outer_resume=1 added={int(added)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('--install',type=Path);q=a.parse_args()
    allowed={'size','active resume identity','active shared restore','active dispatcher suffix','active resume owner','active resume hook',
             'completion local resume','completion root dispatch','completion outer resume','native IPC duplicate root',
             'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.install,p)
        else:print(f'DEFERRED_ACTIVE_RESUME_GEOMETRY verified=1 labels={len(p[2])} exact_restore=1')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('DEFERRED_ACTIVE_RESUME_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
if __name__=='__main__':raise SystemExit(main())
