#!/usr/bin/env python3
"""Private 76-instruction contract stopping before authenticated local bctr."""
import argparse,struct
from pathlib import Path
from audit_formatter_ctr_target import plan as ctr_audit
from analyze_formatter_nested_path import immutable_read
from prepare_formatter_third_contract import plan as third_contract
from prepare_formatter_nested_contract import contract
from prepare_formatter_continuation_plan import plan as continuation
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from guarded_continuation import GUARD
from private_plan_cache import plan_cache_scope

def compare(old,new,cells):
    ob,of,orp,oa,os,ok=old
    nb,nf,nrp,na,ns,nk=new
    root=of[0]
    if nf[:2]!=of[:2] or nf[4]!=of[4] or len(orp)!=74 or len(nrp)!=76 or nrp[:74]!=orp or nrp[74]!=of[2:4]:
        raise ValueError('control contract prefix')
    if len(oa)!=18 or len(na)!=19 or na[:18]!=oa or len(ok)!=4 or len(nk)!=5 or nk[:4]!=ok:
        raise ValueError('control contract accesses')
    if len(cells)!=3 or cells[2][0]!=of[5] or na[18]!=(of[2],of[6],of[5],False,False) or nk[4]!=(of[2],*cells[2]):
        raise ValueError('control contract candidate')
    if os!=ns or len(ns)!=4:
        raise ValueError('control contract slots')
    if len(nf)!=10 or nf[3]!=0x4e800420 or nf[5:7]!=(0,0) or nf[9]!=383*4 or nf[7] in {pc for pc,w in nrp}|{nf[2]}:
        raise ValueError('control contract stop')
    if set(ob)!=set(nb) or any(nb[a]!=ws for a,ws in ob.items() if a!=root):
        raise ValueError('control contract roots')
    for i,w in enumerate(ob[root]):
        if w!=GUARD and (i>=len(nb[root]) or nb[root][i]!=w):
            raise ValueError('control contract old words')
    if not root<nf[7]<root+nf[9] or nf[7]&3 or nb[root][(nf[7]-root)//4]!=nf[8]:
        raise ValueError('control contract target')
    return new

def plan(d,e,*,previous=None,third=None):
    audit,entry,record,cells=ctr_audit(d,e,details=True)
    if audit!=('local_interior',1,'executable',1,1,1,0,1):
        raise ValueError('control contract audit')
    if previous is None:previous=continuation(d,e)
    if third is None:third=third_contract(d,e,previous=previous)
    root=entry[0];_,_,_,_,_,_,_,_,dst,_,_=record
    words=exact_words(d,e,root,383)
    boundary=(dst,exact_words(d,e,dst,1)[0],len(words)*4)
    values={(a,len(blob)):blob for a,blob in cells}
    def resolve(a,n):return values[(a,n)] if (a,n) in values else immutable_read(d,e,a,n)
    new=contract(entry,record,words,previous[0],resolve,control=boundary)
    return compare(third,new,cells)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','control contract prefix','control contract accesses','control contract candidate','control contract slots','control contract stop','control contract roots','control contract old words','control contract target','control contract audit','nested control boundary','nested contract geometry','nested contract parent','nested contract nonvolatile'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            _,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CONTROL_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CONTROL_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} known_data_reads={len(known)} saved_nonvolatile={len(slots)-1} conditional_reads=3 local_target=1 transfer_executed=0 original_execution=0 live_value_verified=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
