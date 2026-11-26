#!/usr/bin/env python3
"""Independent contract for the nested prefix; no live mutable value admitted."""
import argparse,struct
from pathlib import Path
from analyze_formatter_nested_frontier import plan as frontier
from analyze_formatter_nested_path import immutable_read
from prepare_formatter_continuation_plan import plan as continuation
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words

def byte_cells(v,n):
    if v[0]=='const':return tuple(('byte',(v[1]>>(8*(n-1-i)))&255) for i in range(n))
    return tuple(('part',v,n,i) for i in range(n))

def boundary_width(w):
    op,rt,ra,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>1)&1023
    if op in (32,33,34,35,40,41,42,43):
        width=4 if op<=33 else 1 if op<=35 else 2
        update=bool(op&1)
    elif op==31 and not w&1 and xo in (23,55,87,119,279,311,343,375):
        width=4 if xo in (23,55) else 1 if xo in (87,119) else 2
        update=xo in (55,119,311,375)
    else:return 0
    return 0 if rt==1 or (update and (not ra or ra==rt or ra==1)) else width

def contract(entry,record,words,blocks,resolve,*,extended=False,third=False):
    root,initial,parent,caller,readonly=entry
    at,n,path,frame,sites,gp,mem,cr,ctr,lr,saves=record
    if third and extended:raise ValueError('nested contract geometry')
    labels,accesses=(75,18) if third else (45,14) if extended else (36,13)
    if len(path)!=labels or path[0]!=root or len(set(path))!=labels or frame!=48 or len(sites)!=accesses or n!=4:
        raise ValueError('nested contract geometry')
    if initial[1][0]!='stack' or gp[1]!=('stack',initial[1][1]-frame) or lr!=('const',caller):
        raise ValueError('nested contract stack')
    sp=initial[1][1]
    if any(mem.get(a)!=v for a,v in parent.items()):
        raise ValueError('nested contract parent')
    def cells(a,n):return tuple(mem.get(a+i) for i in range(n))
    if cells(sp-frame,4)!=byte_cells(initial[1],4):
        raise ValueError('nested contract backchain')
    if cells(sp+4,4)!=byte_cells(('const',caller),4):
        raise ValueError('nested contract linkage')
    if any(gp[r]!=initial[r] for r in (2,13)):
        raise ValueError('nested contract SDA')
    slots=[(4,32)]
    # Only accept unambiguous preserved incoming nonvolatile values in
    # actual full-word stack stores, and exclude backchain/linkage.
    for r in range(14,32):
        if gp[r]==initial[r]:continue
        matches=[a for a in range(sp-frame+4,sp,4) if cells(a,4)==byte_cells(initial[r],4)]
        if len(matches)!=1 or any(a==matches[0]-sp for a,_ in slots):
            raise ValueError('nested contract nonvolatile')
        slots.append((matches[0]-sp,r))
    if any(pc<root or pc>=root+4*len(words) or pc&3 for pc in path):
        raise ValueError('nested contract path')
    rows=tuple((pc,words[(pc-root)//4]) for pc in path[:-1])
    target=path[-1];w=words[(target-root)//4]
    if boundary_width(w)!=n or blocks.get(root)!=(words[0],GUARD):
        raise ValueError('nested contract boundary')
    known=[]
    for pc,k,width,address in sites:
        if k=='const_read':
            hit=[blob[address-base:address-base+width] for base,blob in readonly if base<=address<address+width<=base+len(blob)]
            if len(hit)>1:raise ValueError('nested contract data')
            data=hit[0] if hit else resolve(address,width)
            if not isinstance(data,bytes) or len(data)!=width:raise ValueError('nested contract data')
            known.append((pc,address,data))
        elif k not in ('stack_write','stack_read'):
            raise ValueError('nested contract access')
    extent=max(path)
    body=tuple(words[(pc-root)//4] if pc in path else GUARD for pc in range(root,extent+4,4))+(GUARD,)
    extended={**blocks,root:body}
    check_spans({a:4*len(ws) for a,ws in extended.items()})
    access=tuple((pc,width,address-sp if k.startswith('stack') else address,k.startswith('stack'),k=='stack_write') for pc,k,width,address in sites)
    return extended,(root,caller,target,w,frame,at,n),rows,access,tuple(slots),tuple(known)

def plan(d,e,*,previous=None):
    counts,kind,entry,record=frontier(d,e,details=True)
    if kind!='writable' or counts[:3]!=(35,35,48):raise ValueError('nested contract predecessor')
    if previous is None:previous=continuation(d,e)
    if previous[3]!=entry[0]:raise ValueError('nested contract predecessor')
    return contract(entry,record,exact_words(d,e,entry[0],383),previous[0],lambda a,n:immutable_read(d,e,a,n))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','nested contract geometry','nested contract stack','nested contract parent','nested contract backchain','nested contract linkage','nested contract SDA','nested contract nonvolatile','nested contract path','nested contract boundary','nested contract data','nested contract access','nested contract predecessor'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        blocks,fields,rows,access,slots,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NESTED_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_NESTED_CONTRACT verified=1 labels={len(rows)} accesses={len(access)} saved_nonvolatile={len(slots)-1} known_data_reads={len(known)} stack_loads={sum(s and not w for _,_,_,s,w in access)} linkage=1 boundary_load_executed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
