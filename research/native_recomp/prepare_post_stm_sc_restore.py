#!/usr/bin/env python3
"""Authenticate the shared SC restore leaf and following version-registration region."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_decision import plan as decision_plan,ROOT,EDGES
from prepare_stm_outer_restore import plan as outer_plan
from prepare_v1337_open_completion import RESTORE,plan as completion
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import first_region,category
from restore_post_stm_v89 import SIZE
from make_v1243_stm_fixture import data_at
from prepare_v625_ipc_client import audit_native

def leaf(words,root,enable,resume):
    if not 4<=len(words)<=16 or resume!=enable+4 or set(words)!=set(range(root,max(words)+4,4)):
        raise ValueError('SC restore extent')
    mf=mt=ret=0
    for pc,(_,w) in words.items():
        op=w>>26;xo=(w>>1)&1023
        rs=(w>>21)&31;ra=(w>>16)&31
        if w==0x4e800020:
            if pc!=max(words):raise ValueError('SC restore return')
            ret+=1
        elif op==31 and xo==83 and rs in (0,*range(3,13)):mf+=1
        elif op==31 and xo==146 and rs in (0,*range(3,13)) and pc==enable:mt+=1
        elif w in (0x4c00012c,0x7c0004ac):pass
        elif op in (20,21,24,25) and not(w&1 and op in (20,21)) and ra in (0,*range(3,13)):pass
        elif op==14 and rs in (0,*range(3,13)):pass
        elif op in (10,11) and not w&0x00200000:pass
        elif op==31 and xo in (28,60,444) and not w&1 and ra in (0,*range(3,13)):pass
        elif op==16 and w&3==0 and (w>>21)&4:
            dst=pc+((w&0xfffc)^0x8000)-0x8000
            if dst<=pc or dst not in words:raise ValueError('SC restore branch')
        elif op==18 and not w&3:
            dst=pc+((w&0x03fffffc)^0x02000000)-0x02000000
            if dst<=pc or dst not in words:raise ValueError('SC restore branch')
        else:raise ValueError('SC restore opcode')
    if (mf,mt,ret)!=(1,1,1):raise ValueError('SC restore control count')
    return len(words)

def plan(d,e):
    prior=decision_plan(d,e)
    _,_,enable,resume,resume_word,words=outer_plan(d,e)
    shared,*_=completion(d,e)
    if any(owner!=RESTORE or shared[RESTORE][(pc-RESTORE)//4]!=w for pc,(owner,w) in words.items()):
        raise ValueError('SC restore identity')
    leaf(words,RESTORE,enable,resume)
    caller=prior[3][-1]+4
    body=exact_words(d,e,ROOT,SIZE//4)
    return (RESTORE,caller,body[(caller-ROOT)//4],enable,resume,resume_word),words

def version_region(d,e,p):
    caller=p[0][1]
    body=exact_words(d,e,ROOT,SIZE//4)
    rows,backs,stores,stops=first_region(ROOT,body,caller)
    if backs or stores or len(stops)!=1 or stops[0][0]!=EDGES[3][0] or stops[0][1]!=1 or stops[0][3]!=EDGES[3][1]:
        raise ValueError('SC version boundary')
    loads=[]
    for pc,w in sorted(rows.items()):
        if category(w)!='load':continue
        op=w>>26;ra=(w>>16)&31;rs=(w>>21)&31
        if op!=32 or ra not in (2,13):raise ValueError('SC version load')
        a=(EXPECTED_GPRS[ra]+((w&0xffff)^0x8000)-0x8000)&0xffffffff
        blob=data_at(d,a,4)
        if blob is None:raise ValueError('SC version data')
        ptr=int.from_bytes(blob,'big')
        if not 0x80004000<=ptr<0x81800000:raise ValueError('SC version pointer')
        text=[]
        for i in range(256):
            ch=data_at(d,ptr+i,1)
            if ch is None:raise ValueError('SC version text')
            if ch==b'\0':break
            if not 32<=ch[0]<127 and ch[0] not in (9,10,13):raise ValueError('SC version text')
            text.append(ch[0])
        else:raise ValueError('SC version text')
        if not text:raise ValueError('SC version text')
        loads.append((pc,rs,a,ptr))
    if len(loads)!=1:raise ValueError('SC version load count')
    return rows,loads

def render(p):
    fields,words=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_post_stm_sc_restore.h"\nnamespace post_stm_sc_restore_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+wr+'};\n'
        'inline constexpr undercover::wii::StmOuterRestoreExpectation expected{'+fmt(fields)+',words};\n}\n')

def audit(root,p):
    _,words=p
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,(root/'main_output.cpp').read_text(),words)
    for pc,(_,w) in words.items():
        if sum(s.count(f'    v1270_before(ctx,0x{pc:08x}u,0x{w:08x}u);') for s in sources)!=1:
            raise ValueError('SC restore hook')
    print(f'POST_STM_SC_RESTORE_TRANSLATION verified=1 labels={len(words)} existing_hooks={len(words)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--out',type=Path);m.add_argument('--audit',type=Path);m.add_argument('--version',action='store_true');q=a.parse_args()
    safe={'size','SC restore extent','SC restore return','SC restore branch','SC restore opcode','SC restore control count','SC restore identity',
          'SC restore hook','SC version boundary','SC version load','SC version data','SC version pointer','SC version text','SC version load count',
          'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.audit:audit(q.audit,p);return 0
        if q.out:
            with (q.out/'private_post_stm_sc_restore.h').open('x') as out:out.write(render(p))
        if q.version:
            rows,loads=version_region(d,e,p)
            print(f'POST_STM_SC_VERSION_GEOMETRY verified=1 labels={len(rows)} pointer_loads={len(loads)} original_string=1 original_execution=0');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_RESTORE_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_RESTORE_GEOMETRY verified=1 labels={len(p[1])} msr_reads=1 msr_writes=1 return=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
