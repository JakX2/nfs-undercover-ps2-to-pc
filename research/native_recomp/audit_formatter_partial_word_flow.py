#!/usr/bin/env python3
"""Conservative first-use census for one incompletely initialized stack word."""
import argparse,struct
from pathlib import Path
from analyze_formatter_after_ctr import plan as after_ctr
from audit_formatter_partial_stack_read import known_mask,consumer
from prepare_formatter_nested_contract import boundary_width
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def role(w):
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    a={ra} if ra else set()
    if op in (14,15):return 'arithmetic',a,{rs}
    if op in (10,11):return 'compare',{ra},set()
    if op in (24,25,26,27,28,29):return 'logical',{rs},{ra}
    if op in (20,21,23):return 'rotate',{rs}|({ra} if op==20 else {rb} if op==23 else set()),{ra}
    if op in (32,33,34,35,40,41,42,43):return 'load_address',a,{rs}|({ra} if op&1 else set())
    if op in (36,37,38,39,44,45):return 'store',a|{rs},({ra} if op&1 else set())
    if op==31:
        if xo in (23,55,87,119,279,311,343,375):return 'load_address',a|{rb},{rs}|({ra} if xo in (55,119,311,375) else set())
        if xo in (151,183,215,247,407,439):return 'store',a|{rb,rs},({ra} if xo in (183,247,439) else set())
        if xo in (444,28,316,60,124,412,284,476):return 'logical',{rs,rb},{ra}
        if xo in (922,954,824):return 'extend_shift',{rs},{ra}
        if xo in (266,40):return 'arithmetic',{ra,rb},{rs}
        if xo in (0,32):return 'compare',{ra,rb},set()
        if xo==339:return 'system_read',set(),{rs}
        if xo==467:return 'system_write',{rs},set()
    if op in (16,18,19):return 'control',None,None
    return 'unsupported',None,None

def first_use(words,loaded,mask):
    if not 0<=loaded<32 or not 1<=len(words)<=12:raise ValueError('partial flow geometry')
    for i,w in enumerate(words,1):
        kind,reads,writes=role(w)
        if reads is None:return i,kind,'unknown',0,0
        if loaded in reads:
            k,independent,overwrite,bits=consumer(w,loaded,mask)
            if k!='other':return i,k,'read',independent,overwrite
            return i,kind,'read',0,int(loaded in writes)
        if loaded in writes:return i,kind,'killed',1,1
    return len(words),'limit','unread',0,0

def plan(d,e):
    kind,path,frame,sites,_,width,region,counts,entry,record,cells=after_ctr(d,e,details=True)
    if (kind,len(path),frame,len(sites),width,region,counts)!=('stack_load',84,48,21,4,'child_local',(2,0)):
        raise ValueError('partial flow predecessor')
    at,n,full,_,_,gp,mem,cr,ctr,lr,saves=record
    pc=full[-1];root=entry[0];remaining=(root+383*4-pc)//4
    if not 2<=remaining<=383:raise ValueError('partial flow geometry')
    words=exact_words(d,e,pc,min(remaining,13))
    if boundary_width(words[0])!=4:raise ValueError('partial flow load')
    loaded=(words[0]>>21)&31
    return first_use(words[1:],loaded,known_mask(mem,at,n))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','partial flow geometry','partial flow predecessor','partial flow load'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            offset,kind,use,independent,overwrite=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_FLOW verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_FLOW verified=1 next_use_offset={offset} class={kind} use={use} independent_of_unknown={independent} overwrites_loaded_register={overwrite} value_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
