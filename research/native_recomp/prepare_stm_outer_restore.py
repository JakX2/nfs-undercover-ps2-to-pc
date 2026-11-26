#!/usr/bin/env python3
"""Authenticate the actual outer OSRestoreInterrupts and rising-EE boundary privately."""
import argparse
import struct
from pathlib import Path
from prepare_v1337_open_completion import plan as completion,RESTORE
from prepare_v629_stm_open import geometry,STM,EDGES
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct

def select(root,body,labels):
    sites=[pc for pc in labels if body[(pc-root)//4]>>26==31 and (body[(pc-root)//4]>>1)&1023==146]
    if len(sites)!=1 or sites[0]+4 not in labels:raise ValueError('outer restore MSR site')
    return sites[0],sites[0]+4

def plan(d,e):
    shared,*_=completion(d,e)
    _,body,_,_,_,_=geometry(d,e)
    call,dst=EDGES[-1]
    if dst!=RESTORE or direct_bl(body[(call-STM)//4],call)!=RESTORE:raise ValueError('outer restore call')
    ws=shared[RESTORE]
    labels=reachable(RESTORE,ws)
    enable,resume=select(RESTORE,ws,labels)
    caller=call+4;caller_word=body[(caller-STM)//4]
    return caller,caller_word,enable,resume,ws[(resume-RESTORE)//4],{pc:(RESTORE,ws[(pc-RESTORE)//4]) for pc in labels}

def render(p):
    caller,caller_word,enable,resume,resume_word,words=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_stm_outer_restore.h"\nnamespace stm_outer_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+rows+'};\n'
        'inline constexpr undercover::wii::StmOuterRestoreExpectation expected{'+fmt((RESTORE,caller,caller_word,enable,resume,resume_word))+',words};\n}\n')

def verify(root,p):
    caller,_,_,_,_,words=p
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,(root/'main_output.cpp').read_text(),words)
    hits=[s for s in sources if f'loc_{caller-4:X}: ;' in s]
    if len(hits)!=1:raise ValueError('outer restore native call')
    verify_direct(hits[0],caller-4,RESTORE)
    for pc,(_,word) in words.items():
        hook=f'    v1270_before(ctx,0x{pc:08x}u,0x{word:08x}u);'
        if sum(s.count(hook) for s in sources)!=1:raise ValueError('outer restore native hook')
    print(f'STM_OUTER_RESTORE_TRANSLATION verified=1 labels={len(words)} reused_hooks={len(words)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    allowed={'size','outer restore MSR site','outer restore call','outer restore native call','outer restore native hook',
        'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
        'helper call label','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:verify(q.out,p)
        else:
            with (q.out/'private_stm_outer_restore.h').open('x') as f:f.write(render(p))
            print(f'STM_OUTER_RESTORE_PRIVATE verified=1 labels={len(p[-1])} enable_sites=1')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('STM_OUTER_RESTORE_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
if __name__=='__main__':raise SystemExit(main())
