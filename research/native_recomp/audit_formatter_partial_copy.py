#!/usr/bin/env python3
"""Private symbolic-only continuation of the authenticated mixed stack word."""
import argparse,struct
from pathlib import Path
from analyze_formatter_after_ctr import plan as after_ctr
from analyze_formatter_nested_path import immutable_read
from audit_formatter_partial_word_flow import first_use
from audit_formatter_partial_stack_read import known_mask
from prepare_post_stm_sc_report_formatter_path import first_path
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def store_shape(w,loaded):
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    d={36:4,37:4,38:1,39:1,44:2,45:2}
    x={151:4,183:4,215:1,247:1,407:2,439:2}
    if op in d:return d[op],int(rs==loaded),int(ra!=0 and ra==loaded)
    if op==31 and xo in x and not w&1:return x[xo],int(rs==loaded),int((ra!=0 and ra==loaded) or rb==loaded)
    raise ValueError('partial copy store form')

def copied_cells(mem,origin):
    return sum(v[0]=='uninitialized' and not origin<=at<origin+4 for at,v in mem.items())

def plan(d,e):
    kind,path,frame,sites,_,width,region,counts,entry,record,cells=after_ctr(d,e,details=True)
    if (kind,len(path),frame,len(sites),width,region,counts)!=('stack_load',84,48,21,4,'child_local',(2,0)):
        raise ValueError('partial copy predecessor')
    at,n,full,_,_,gp,mem,cr,ctr,lr,saves=record
    root,initial,parent,caller,readonly=entry
    ws=exact_words(d,e,root,383);pc=full[-1];i=(pc-root)//4
    loaded=(ws[i]>>21)&31
    offset,k,use,_,_=first_use(ws[i+1:i+13],loaded,known_mask(mem,at,n))
    if (offset,k,use)!=(4,'store','read'):raise ValueError('partial copy first use')
    store=ws[i+offset];sw,source,address=store_shape(store,loaded)
    allowed={(a,len(blob)):blob for a,blob in cells}
    seen=[];extra=set()
    def resolve(a,n):
        if (a,n) in allowed:return allowed[a,n]
        extra.add((a,n))
        if len(extra)>32:raise ValueError('partial copy data cap')
        return immutable_read(d,e,a,n)
    def observe(pc,w,gp,mem):
        seen.append((pc,w,gp,mem))
    state=(gp,mem,cr,ctr,lr,frame,saves)
    reason='call'
    try:
        first_path(root,ws,{}, {},readonly,initial[1][1],start=pc,resume=state,details=True,
                   read_resolver=resolve,partial_origin=(at,n),step_observer=observe,entry_lr=lr)
    except ValueError as ex:
        # Only aggregate classes are exposed, not private words, addresses or data.
        reason={'formatter unknown value':'unknown_value','formatter unknown arithmetic':'unknown_arithmetic',
                'formatter stack read provenance':'stack_read','formatter pointer provenance':'pointer',
                'formatter protected stack write':'protected_write','formatter stack write provenance':'stack_write',
                'formatter indexed store provenance':'indexed_store','formatter indexed load provenance':'indexed_load',
                'formatter data read provenance':'data_read','nested data not immutable':'data_read',
                'formatter other boundary':'control','formatter CR provenance':'condition',
                'formatter CTR provenance':'counter','formatter path bound':'path_bound'}.get(str(ex),'other')
    if len(seen)<2 or seen[0][0]!=pc or seen[1][2][loaded][0]!='partial':
        raise ValueError('partial copy load witness')
    # The observer is pre-instruction. A following observation proves the
    # preceding symbolic step finished; the last observed instruction did not.
    store_seen=len(seen)>offset and seen[offset][0]==pc+4*offset and seen[offset][1]==store
    store_done=store_seen and len(seen)>offset+1
    copied=copied_cells(seen[offset+1][3],at) if store_done else 0
    peak=max(copied_cells(row[3],at) for row in seen)
    return sw,source,address,int(store_seen),int(store_done),copied,peak,len(seen)-1,reason

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','partial copy predecessor','partial copy first use','partial copy store form','partial copy load witness'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            width,source,address,seen,done,copied,peak,visits,reason=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_COPY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_COPY verified=1 store_width={width} source_dependency={source} address_dependency={address} store_seen={seen} store_symbolic={done} copied_unknown_bytes={copied} peak_unknown_copies={peak} symbolic_steps={visits} boundary={reason} value_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
