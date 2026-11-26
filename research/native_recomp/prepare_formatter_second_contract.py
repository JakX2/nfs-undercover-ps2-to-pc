#!/usr/bin/env python3
"""Second finite prefix with one conditional data value checked at native load."""
import argparse,struct
from pathlib import Path
from analyze_formatter_second_frontier import plan as second_frontier
from analyze_formatter_nested_path import immutable_read
from prepare_formatter_nested_contract import plan as first_contract,contract
from prepare_formatter_continuation_plan import plan as continuation
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from guarded_continuation import GUARD

def compare(old,new,cell):
    ob,of,orp,oa,os,ok=old
    nb,nf,nrp,na,ns,nk=new
    root=of[0]
    if nf[:2]!=of[:2] or nf[4]!=of[4] or len(orp)!=35 or len(nrp)!=44 or nrp[:35]!=orp or nrp[35]!=of[2:4]:
        raise ValueError('second contract prefix')
    if len(oa)!=13 or len(na)!=14 or na[:13]!=oa or len(ok)!=1 or len(nk)!=2 or nk[:1]!=ok:
        raise ValueError('second contract accesses')
    if na[13]!=(of[2],of[6],of[5],False,False) or nk[1]!=(of[2],cell[0],cell[1]) or cell[0]!=of[5]:
        raise ValueError('second contract candidate')
    if os!=ns:
        raise ValueError('second contract slots')
    if set(ob)!=set(nb) or any(nb[a]!=ws for a,ws in ob.items() if a!=root):
        raise ValueError('second contract roots')
    for i,w in enumerate(ob[root]):
        if w!=GUARD and (i>=len(nb[root]) or nb[root][i]!=w):
            raise ValueError('second contract old words')
    return new

def plan(d,e,*,previous=None,first=None):
    counts,kind,mapped,equal,entry,record,cell=second_frontier(d,e,details=True)
    if counts[:4]!=(44,44,9,48) or (kind,mapped,equal)!=('writable',1,1):
        raise ValueError('second contract frontier')
    if previous is None:previous=continuation(d,e)
    if first is None:first=first_contract(d,e,previous=previous)
    def resolve(a,n):
        if (a,n)==(cell[0],len(cell[1])):return cell[1]
        return immutable_read(d,e,a,n)
    new=contract(entry,record,exact_words(d,e,entry[0],383),previous[0],resolve,extended=True)
    return compare(first,new,cell)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','second contract frontier','second contract prefix','second contract accesses','second contract candidate','second contract slots','second contract roots','second contract old words'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        _,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_SECOND_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_SECOND_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} saved_nonvolatile={len(slots)-1} known_data_reads={len(known)} conditional_reads=1 unresolved_loads=1 original_execution=0 live_value_verified=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
