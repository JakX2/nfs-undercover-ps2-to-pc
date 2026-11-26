#!/usr/bin/env python3
"""Derive the next finite prefix with both prior mutable loads checked."""
import argparse,struct
from pathlib import Path
from analyze_formatter_two_cell_path import plan as two_cell_path
from analyze_formatter_nested_path import immutable_read
from prepare_formatter_second_contract import plan as second_contract
from prepare_formatter_nested_contract import contract
from prepare_formatter_continuation_plan import plan as continuation
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from guarded_continuation import GUARD

def compare(old,new,cells):
    ob,of,orp,oa,os,ok=old
    nb,nf,nrp,na,ns,nk=new
    root=of[0]
    if nf[:2]!=of[:2] or nf[4]!=of[4] or len(orp)!=44 or len(nrp)!=74 or nrp[:44]!=orp or nrp[44]!=of[2:4]:
        raise ValueError('third contract prefix')
    if len(oa)!=14 or len(na)!=18 or na[:14]!=oa or len(ok)!=2 or nk[:2]!=ok:
        raise ValueError('third contract accesses')
    if sum(not w for _,_,_,_,w in na)!=5 or sum(w for _,_,_,_,w in na)!=13:
        raise ValueError('third contract counts')
    if len(cells)!=2 or cells[1][0]!=of[5] or na[14]!=(of[2],of[6],of[5],False,False) or nk[2]!=(of[2],*cells[1]):
        raise ValueError('third contract candidate')
    if not set(os).issubset(ns):raise ValueError('third contract slots')
    if set(ob)!=set(nb) or any(nb[a]!=ws for a,ws in ob.items() if a!=root):
        raise ValueError('third contract roots')
    for i,w in enumerate(ob[root]):
        if w!=GUARD and (i>=len(nb[root]) or nb[root][i]!=w):
            raise ValueError('third contract old words')
    return new

def plan(d,e,*,previous=None,second=None):
    kind,path,frame,sites,words,width,section,entry,record,cells=two_cell_path(d,e,details=True)
    if (kind,len(path),len(set(path)),frame,len(sites),width,section)!=('load',74,74,48,18,4,'writable'):
        raise ValueError('third contract frontier')
    if previous is None:previous=continuation(d,e)
    if second is None:second=second_contract(d,e,previous=previous)
    values={(a,len(blob)):blob for a,blob in cells}
    def resolve(a,n):
        return values[(a,n)] if (a,n) in values else immutable_read(d,e,a,n)
    new=contract(entry,record,exact_words(d,e,entry[0],383),previous[0],resolve,third=True)
    return compare(second,new,cells)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','third contract frontier','third contract prefix','third contract accesses','third contract counts','third contract candidate','third contract slots','third contract roots','third contract old words','nested contract nonvolatile','nested contract parent','nested contract linkage'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        _,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_THIRD_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_THIRD_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} saved_nonvolatile={len(slots)-1} known_data_reads={len(known)} stack_loads={sum(s and not w for _,_,_,s,w in access)} conditional_reads=2 unresolved_loads=1 original_execution=0 live_value_verified=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
