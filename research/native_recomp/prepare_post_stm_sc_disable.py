#!/usr/bin/env python3
"""Authenticate the shared original interrupt-disable leaf and next SC decision."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_join import plan as entry_plan,ROOT,EDGES
from prepare_v1337_open_completion import plan as completion,DISABLE
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from prepare_stm_event_return_geometry import object_at
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import first_region,category
from prepare_owner_scheduler_v722 import reachable
from restore_post_stm_v89 import SIZE
BLR=0x4e800020

def leaf(words):
    if not 3<=len(words)<=12 or words[-1]!=BLR or words.count(BLR)!=1:
        raise ValueError('disable extent')
    mf=mt=0
    for w in words[:-1]:
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31
        if op==31 and xo==83 and rs in (0,*range(3,13)):mf+=1
        elif op==31 and xo==146 and rs in (0,*range(3,13)):mt+=1
        elif w in (0x4c00012c,0x7c0004ac):pass
        elif op in (21,24,25) and not(w&1 and op==21) and ra in (0,*range(3,13)):pass
        elif op==14 and rs in (0,*range(3,13)):pass
        elif op==31 and xo in (28,60,444) and not w&1 and ra in (0,*range(3,13)):pass
        else:raise ValueError('disable opcode')
    if mf!=1 or mt!=1:raise ValueError('disable MSR count')
    return len(words)

def plan(d,e):
    fields,slots,_,_=entry_plan(d,e)
    shared,*_=completion(d,e)
    ws=shared[DISABLE]
    if fields[2]!=DISABLE or fields[3]!=ws[0] or len(reachable(DISABLE,ws))!=len(ws):
        raise ValueError('disable identity')
    count=leaf(ws)
    caller=EDGES[0][0]+4
    body=exact_words(d,e,ROOT,SIZE//4)
    rows,backs,stores,stops=first_region(ROOT,body,caller)
    if backs or stores or not stops or any(k!=1 or (pc,dst) not in EDGES for pc,k,_,dst in stops):
        raise ValueError('SC first decision')
    loads=[]
    for pc,w in sorted(rows.items()):
        if category(w)!='load':continue
        op=w>>26;ra=(w>>16)&31
        if op not in (32,34,40) or ra not in (2,13):raise ValueError('SC decision load')
        n={32:4,34:1,40:2}[op]
        a=(EXPECTED_GPRS[ra]+((w&0xffff)^0x8000)-0x8000)&0xffffffff
        loads.append((pc,a,n,object_at(d,e,a,n)))
    return (DISABLE,caller,body[(caller-ROOT)//4]),tuple(ws),rows,loads,stops

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','disable extent','disable opcode','disable MSR count','disable identity','SC first decision',
          'SC decision load','STM object identity','STM data request','STM object range'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        fields,words,rows,loads,stops=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_DISABLE_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_DISABLE_GEOMETRY verified=1 leaf_labels={len(words)} msr_reads=1 msr_writes=1 caller=1 decision_labels={len(rows)} decision_loads={len(loads)} decision_calls={len(stops)} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
