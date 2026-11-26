#!/usr/bin/env python3
"""Private bridge from the stronger STM lane to the previously verified SC startup."""
import argparse
import struct
from pathlib import Path
from prepare_stm_final_return import plan as final_plan,prologue
from restore_post_stm_v89 import OS_CALL,ROOT,SIZE,EDGES
from prepare_v1337_open_completion import plan as completion,DISABLE
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v1377_stm_tail import scan
from audit_osinit_suffix_v929 import first_region,category

def prefix(root,words,site,target):
    rows,backs,stores,stops=first_region(root,words,root)
    if backs or len(stops)!=1 or stops[0]!=(site,1,1,target) or set(rows)!=set(range(root,site+4,4)):
        raise ValueError('SC first boundary')
    for pc,w in rows.items():
        op=w>>26;ra=(w>>16)&31
        if pc==site:continue
        kind=category(w)
        if kind=='store':
            if op not in (36,37,47) or ra!=1:raise ValueError('SC first store')
        elif kind=='load':
            if op not in (32,46) or ra!=1:raise ValueError('SC first load')
        elif kind!='integer':raise ValueError('SC first opcode')
    frame,saved=prologue(tuple(rows[pc] for pc in range(root,site,4)))
    if not frame or 'lr' not in saved.values():raise ValueError('SC frame')
    return len(rows),stores,len(saved)-1

def derive(d,e):
    fields,_,_,_,_,_=final_plan(d,e)
    if fields[2]!=OS_CALL or direct_bl(fields[3],OS_CALL)!=ROOT:
        raise ValueError('SC caller')
    if parse_functions(e).get(ROOT)!=SIZE:raise ValueError('SC extent')
    body=exact_words(d,e,ROOT,SIZE//4)
    if body[-1]!=0x4e800020:raise ValueError('SC return')
    reachable,calls,returns,_,_=scan(ROOT,body,ROOT,dict(EDGES))
    if calls!=set(EDGES) or len(returns)!=1:raise ValueError('SC call closure')
    site,target=EDGES[0]
    shared,*_=completion(d,e)
    if target!=DISABLE or tuple(shared[DISABLE])!=tuple(exact_words(d,e,DISABLE,len(shared[DISABLE]))):
        raise ValueError('SC shared helper')
    labels,stores,saved=prefix(ROOT,body,site,target)
    return len(reachable),len(calls),labels,stores,saved

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC caller','SC extent','SC return','SC call closure','SC shared helper','SC first boundary',
          'SC first store','SC first load','SC first opcode','SC frame','tail extent','tail escape','tail call','tail control',
          'tail reachability','prologue identity','prologue slot','prologue frame','region coverage','unsupported boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        reachable,calls,labels,stores,saved=derive(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_JOIN_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_JOIN_GEOMETRY verified=1 original_caller=1 subsystem_labels={reachable} direct_edges={calls} first_labels={labels} stack_stores={stores} saved_gprs={saved} shared_disable=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
