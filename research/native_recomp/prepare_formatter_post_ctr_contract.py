#!/usr/bin/env python3
"""Private contract for the completed post-CTR path, before partial stack read."""
import argparse,struct
from pathlib import Path
from analyze_formatter_after_ctr import plan as after_ctr
from analyze_formatter_nested_path import immutable_read
from prepare_formatter_control_contract import plan as control_plan
from prepare_formatter_nested_contract import contract
from prepare_formatter_continuation_plan import plan as continuation
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from guarded_continuation import GUARD
from private_plan_cache import plan_cache_scope

def compare(old,new):
    ob,of,orp,oa,os,ok=old
    nb,nf,nrp,na,ns,nk=new
    root=of[0]
    if nf[:2]!=of[:2] or nf[4]!=of[4] or len(orp)!=76 or len(nrp)!=84 or nrp[:76]!=orp or nrp[76]!=of[2:4] or nrp[77]!=of[7:9]:
        raise ValueError('post CTR contract prefix')
    if len(oa)!=19 or len(na)!=21 or na[:19]!=oa or len(ok)!=5 or nk[:5]!=ok:
        raise ValueError('post CTR contract access')
    if sum(x[4] for x in na)!=13 or sum(not x[4] for x in na)!=8 or len(nk)!=sum(not x[3] and not x[4] for x in na):
        raise ValueError('post CTR contract census')
    if not set(os)<=set(ns) or len(ns)>19:
        raise ValueError('post CTR contract slots')
    if len(nf)!=7 or nf[6]!=4 or nf[5]%4 or not -44<=nf[5]<=-4 or nf[2] in {pc for pc,w in nrp}:
        raise ValueError('post CTR contract boundary')
    if set(ob)!=set(nb) or any(nb[a]!=ws for a,ws in ob.items() if a!=root):
        raise ValueError('post CTR contract roots')
    for i,w in enumerate(ob[root]):
        if w!=GUARD and (i>=len(nb[root]) or nb[root][i]!=w):
            raise ValueError('post CTR contract old words')
    return new

def plan(d,e,*,previous=None,control=None):
    kind,path,frame,sites,_,width,region,counts,entry,record,cells=after_ctr(d,e,details=True)
    if (kind,len(path),len(set(path)),frame,len(sites),width,region,counts)!=('stack_load',84,84,48,21,4,'child_local',(2,0)):
        raise ValueError('post CTR contract predecessor')
    if previous is None:previous=continuation(d,e)
    if control is None:control=control_plan(d,e,previous=previous)
    values={(a,len(blob)):blob for a,blob in cells}
    def resolve(a,n):return values[(a,n)] if (a,n) in values else immutable_read(d,e,a,n)
    new=contract(entry,record,exact_words(d,e,entry[0],383),previous[0],resolve,stack_boundary=True)
    return compare(control,new)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post CTR contract prefix','post CTR contract access','post CTR contract census','post CTR contract slots','post CTR contract boundary','post CTR contract roots','post CTR contract old words','post CTR contract predecessor','nested stack boundary','nested contract geometry','nested contract nonvolatile'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            _,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_POST_CTR_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_POST_CTR_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} known_data_reads={len(known)} stack_loads={sum(s and not w for _,_,_,s,w in access)} saved_nonvolatile={len(slots)-1} local_edge=1 stack_stop=1 unknown_bytes_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
