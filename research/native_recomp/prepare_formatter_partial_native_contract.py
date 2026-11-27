#!/usr/bin/env python3
"""Private 95-instruction contract, stopping before the next unknown opcode.

The load uses existing live bytes conditionally. This contract does not assign
their values or authorize arbitrary writes in the parent frame.
"""
import argparse,struct
from pathlib import Path
from audit_formatter_partial_copy import plan as replay_plan,caller_store_candidate,boundary_shape,store_location
from audit_formatter_partial_stack_read import known_mask
from prepare_formatter_post_ctr_contract import plan as post_plan
from prepare_formatter_nested_contract import boundary_width,byte_cells
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from private_plan_cache import plan_cache_scope

def read_address(w,gp):
    width=boundary_width(w)
    if not width:return None
    op,ra,rb=w>>26,(w>>16)&31,(w>>11)&31
    a=gp[ra] if ra else ('const',0)
    b=gp[rb] if op==31 else ('const',((w&0xffff)^0x8000)-0x8000)
    if a[0]=='const' and b[0]=='stack':a,b=b,a
    if a[0] not in ('stack','const') or b[0]!='const':raise ValueError('partial native read address')
    off=((b[1]&0xffffffff)^0x80000000)-0x80000000
    at=a[1]+off
    if a[0]=='const':at&=0xffffffff
    if at%width:raise ValueError('partial native read address')
    return a[0],at,width

def read_value(cells,w):
    n=len(cells)
    if all(c is not None and c[0]=='byte' for c in cells):
        v=int.from_bytes(bytes(c[1] for c in cells),'big')
        op,xo=w>>26,(w>>1)&1023
        if n==2 and (op in (42,43) or op==31 and xo in (343,375)) and v&0x8000:v|=0xffff0000
        return ('const',v)
    if all(c is not None and c[0]=='part' and c[1]==cells[0][1] and c[2:]==(n,i) for i,c in enumerate(cells)):
        return cells[0][1]
    if all(c is not None for c in cells) and any(c[0]=='uninitialized' for c in cells):
        return ('partial',(('byte',0),)*(4-n)+tuple(cells))
    raise ValueError('partial native read provenance')

def extra_census(trace,admitted,entry):
    _,initial,parent,_,_=entry;sp=initial[1][1]
    sites={row[0] for row in admitted};counts={}
    for i,(pc,w,gp,mem) in enumerate(trace[:-1]):
        if not i or pc in sites:continue
        family=boundary_shape(w);changed=mem!=trace[i+1][3]
        if family in ('load','store','floating_load','floating_store','paired_single_memory') or changed:
            if family=='load':
                try:
                    k,a,n=read_address(w,gp)
                    region=('child' if sp-48<=a<a+n<=sp else 'caller' if sp<=a<a+n<=sp+704 else 'outside') if k=='stack' else 'absolute'
                    initialized=sum(a+j in mem for j in range(n)) if k=='stack' else 0
                    key=(family,region,n,initialized,int(changed))
                except (ValueError,TypeError):key=(family,'unresolved',0,0,int(changed))
            elif family=='store':
                n,region,prior,_,_,_=store_location(w,gp,mem,parent,sp,48)
                key=(family,region,n,prior,int(changed))
            else:key=(family,'other',0,0,int(changed))
            counts[key]=counts.get(key,0)+1
    return counts

def extend(old,trace,admitted,entry,record,words):
    blocks,fields,rows,access,slots,known=old
    root,caller,start,load,frame,offset,width=fields
    root2,initial,parent,caller2,_=entry
    at,n,path,_,_,_,mem,_,_,_,_=record
    sp=initial[1][1]
    if (root,caller)!=(root2,caller2) or (frame,width,n,at-sp)!=(48,4,4,offset) or len(rows)!=84 or len(access)!=21 or len(known)!=5:
        raise ValueError('partial native predecessor')
    if len(trace)!=12 or len(admitted)!=4 or trace[0][:2]!=(start,load) or tuple(path[:-1])!=tuple(pc for pc,_ in rows):
        raise ValueError('partial native path')
    if len(words)!=383 or boundary_width(load)!=4 or known_mask(mem,at,n).bit_count()!=16 or trace[0][3]!=mem:
        raise ValueError('partial native origin')
    extra=tuple((pc,w) for pc,w,_,_ in trace[:-1]);target,word,last_gp,last_mem=trace[-1]
    all_rows=tuple(rows)+extra
    live={pc for pc,_ in all_rows}|{target}
    if len(live)!=96 or any(pc&3 or not root<=pc<root+4*len(words) or words[(pc-root)//4]!=w or w==GUARD for pc,w in all_rows+((target,word),)):
        raise ValueError('partial native words')
    if boundary_shape(word)!='integer':raise ValueError('partial native boundary')
    candidate={pc:(a,w,k) for pc,a,w,k in admitted}
    if len(candidate)!=4 or sum(w for _,w,_ in candidate.values())!=16:raise ValueError('partial native caller sites')
    extra_access=[(start,4,offset,True,False)]
    touched=set();partial_count=0
    loaded=(load>>21)&31
    for i,(pc,w,gp,before) in enumerate(trace[:-1]):
        _,_,after_gp,after=trace[i+1]
        if i==0:
            cells=tuple(mem.get(at+j,('uninitialized',at+j)) for j in range(4))
            if after_gp[loaded]!=('partial',cells) or before!=after:raise ValueError('partial native load')
        elif pc in candidate:
            a,n,k=candidate[pc]
            if caller_store_candidate(trace[i],parent,sp,frame,k)!=(pc,a,n,k) or n!=4 or not sp+8<=a<a+n<=sp+704 or any(j in touched for j in range(a,a+n)):
                raise ValueError('partial native caller sites')
            src=gp[(w>>21)&31]
            data=src[1] if k=='partial' else byte_cells(src,n)
            expected={**before,**{a+j:c for j,c in enumerate(data)}}
            if after!=expected:raise ValueError('partial native caller effects')
            touched.update(range(a,a+n));partial_count+=int(k=='partial')
            extra_access.append((pc,n,a-sp,True,True))
        elif boundary_shape(w)=='load':
            k,a,n=read_address(w,gp) or ('unknown',0,0)
            if k!='stack' or not sp-frame<=a<a+n<=sp+704 or before!=after:
                raise ValueError('partial native extra access')
            cells=tuple(before.get(a+j) for j in range(n))
            if after_gp[(w>>21)&31]!=read_value(cells,w):raise ValueError('partial native read provenance')
            extra_access.append((pc,n,a-sp,True,False))
        elif boundary_shape(w) in ('store','floating_load','floating_store','paired_single_memory') or before!=after:
            raise ValueError('partial native extra access')
    if not 5<=len(extra_access)<=11 or len(touched)!=16 or partial_count!=1 or any(last_mem.get(a)!=v for a,v in parent.items()):
        raise ValueError('partial native caller effects')
    if last_gp[1]!=initial[1][:1]+(sp-frame,) or any(last_gp[r]!=initial[r] for r in (2,13)):
        raise ValueError('partial native ABI')
    for off,r in slots:
        v=('const',caller) if r==32 else initial[r]
        if tuple(last_mem.get(sp+off+j) for j in range(4))!=byte_cells(v,4):
            raise ValueError('partial native ABI')
    if any(last_gp[r]!=initial[r] and r not in {r for _,r in slots} for r in range(14,32)):
        raise ValueError('partial native ABI')
    old_body=blocks[root]
    body=tuple(words[(pc-root)//4] if pc in live else GUARD for pc in range(root,max(live)+4,4))+(GUARD,)
    if any(w!=GUARD and (i>=len(body) or body[i]!=w) for i,w in enumerate(old_body)):raise ValueError('partial native old words')
    expanded={**blocks,root:body}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    return expanded,(root,caller,target,word,frame,0,0),all_rows,tuple(access)+tuple(extra_access),slots,known

def plan(d,e,*,previous=None,control=None,post=None,report=False):
    result,extra,trace,admitted,entry,record=replay_plan(d,e,details=True)
    if result[3:9]!=(1,1,2,2,11,'other') or result[-1]!=(4,4) or extra!=('integer',11,1,16):
        raise ValueError('partial native replay')
    if report:
        for (family,region,width,prior,changed),count in sorted(extra_census(trace,admitted,entry).items()):
            print(f'FORMATTER_PARTIAL_EXTRA family={family} region={region} width={width} prior_bytes={prior} memory_changed={changed} count={count}')
    if post is None:post=post_plan(d,e,previous=previous,control=control)
    return extend(post,trace,admitted,entry,record,exact_words(d,e,entry[0],383))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','partial native predecessor','partial native path','partial native origin','partial native words','partial native boundary','partial native caller sites','partial native load','partial native caller effects','partial native extra access','partial native read address','partial native read provenance','partial native ABI','partial native old words','partial native replay'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():_,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes(),report=True)
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_NATIVE_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_NATIVE_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} loads={sum(not x[4] for x in access)} stores={sum(x[4] for x in access)} caller_stores=4 conditional_stack_load=1 known_data_reads={len(known)} saved_nonvolatile={len(slots)-1} boundary=instruction unknown_bytes_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
