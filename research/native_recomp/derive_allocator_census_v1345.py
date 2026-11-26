#!/usr/bin/env python3
"""Original allocator-free structural census. No private words are published."""
import argparse,struct
from pathlib import Path
from prepare_v1337_open_completion import plan,FREE,DISABLE,RESTORE
from prepare_owner_scheduler_v722 import reachable
from prepare_v419_full_start import MAX_DOL,direct_bl

D_STORES={36:4,37:4,38:1,39:1,44:2,45:2,47:0}
X_STORES={151:4,183:4,215:1,247:1,407:2,439:2}
def store_form(w):
    op=w>>26;xo=(w>>1)&1023;ra=(w>>16)&31;rs=(w>>21)&31
    if op in D_STORES:
        width=D_STORES[op] or 4*(32-rs)
        return ('multiple' if op==47 else 'scalar',width,ra,op in (37,39,45))
    if op==31 and xo in X_STORES:
        return ('indexed',X_STORES[xo],ra,xo in (183,247,439))
    # FP, paired-single, byte-reversed, string, conditional and cache-line
    # stores are not admitted silently by this allocator-specific analysis.
    if op in (52,53,54,55,60,61) or op==31 and xo in (150,661,725,662,918,663,695,727,759,983,1014):
        raise ValueError('allocator unsupported store')
    return None

def census(root,words,edges):
    if len(words)>512 or not words:raise ValueError('allocator extent')
    rows=reachable(root,words);calls=set();returns=0;counts={}
    for pc in rows:
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==18 and w&1:
            dst=direct_bl(w,pc)
            if (pc,dst) not in edges:raise ValueError('allocator call')
            calls.add((pc,dst))
        elif op==17 or op==19 and (xo in (50,528) or (xo==16 and w&1)) or op==31 and xo==146 or op==16 and w&1:
            raise ValueError('allocator control')
        if op==19 and xo==16 and not(w&1):returns+=1
        st=store_form(w)
        if st:
            form,width,ra,update=st
            k=(form,'stack' if ra==1 else 'sda' if ra in (2,13) else 'other',width,update)
            counts[k]=counts.get(k,0)+1
    if calls!=set(edges) or not returns or not counts:raise ValueError('allocator coverage')
    return len(rows),returns,counts

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        shared,edges,*_=plan(a.dol.read_bytes(),a.elf.read_bytes())
        calls=tuple((lr-4,dst) for dst,lr,_,_ in edges[3:5])
        if tuple(dst for _,dst in calls)!=(DISABLE,RESTORE):raise ValueError('allocator call')
        n,ret,counts=census(FREE,shared[FREE],calls)
        print(f'V1345_ALLOCATOR_CENSUS verified=1 labels={n} direct_edges=2 returns={ret} stores={sum(counts.values())} original_execution=0')
        for (form,base,width,update),count in sorted(counts.items()):
            print(f'V1345_ALLOCATOR_STORE form={form} base={base} width={width} update={int(update)} count={count}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','allocator extent','allocator unsupported store','allocator call','allocator control','allocator coverage','reachable fallthrough','reachable external conditional')
        print('V1345_ALLOCATOR_CENSUS verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
