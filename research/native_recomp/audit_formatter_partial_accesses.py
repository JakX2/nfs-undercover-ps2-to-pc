#!/usr/bin/env python3
"""Redacted census of completed memory accesses and next integer boundary."""
import argparse,struct
from pathlib import Path
from audit_formatter_partial_copy import plan as replay,store_location,boundary_shape
from audit_formatter_nested_read import classify_section
from prepare_formatter_nested_contract import boundary_width
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def load_geometry(w,gp):
    op,ra,rb,xo=w>>26,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    n=boundary_width(w)
    if not n:return None
    a=gp[ra] if ra else ('const',0)
    if op==31:b=gp[rb]
    else:b=('const',((w&0xffff)^0x8000)-0x8000)
    if a[0]=='const' and b[0]=='stack':a,b=b,a
    if a[0] not in ('const','stack') or b[0]!='const':raise ValueError('partial audit load address')
    off=((b[1]&0xffffffff)^0x80000000)-0x80000000
    at=a[1]+off
    if a[0]=='const':at&=0xffffffff
    return a[0],at,n

def integer_shape(w,gp):
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    d={7:'mulli',8:'subfic',12:'addic',13:'addic_record',14:'addi',15:'addis',24:'ori',25:'oris',26:'xori',27:'xoris',28:'andi_record',29:'andis_record'}
    x={8:'subfc',10:'addc',24:'slw',26:'cntlzw',28:'and',40:'subf',60:'andc',104:'neg',124:'nor',136:'subfe',138:'adde',200:'subfze',202:'addze',232:'subfme',234:'addme',235:'mullw',266:'add',284:'eqv',316:'xor',412:'orc',444:'or',459:'divwu',476:'nand',491:'divw',536:'srw',792:'sraw',824:'srawi',922:'extsh',954:'extsb'}
    if op in d:
        regs=(rs,) if op>=24 else (() if op in (14,15) and ra==0 else (ra,))
        name=d[op]
    elif op==31 and xo in x:
        name=x[xo]
        if xo in (26,824,922,954):regs=(rs,)
        elif xo in (104,200,202,232,234):regs=(ra,)
        elif xo in (8,10,40,136,138,235,266,459,491):regs=(ra,rb)
        else:regs=(rs,rb)
    else:return 'other',0,0,0
    return name,len(regs),sum(gp[r][0]=='partial' for r in regs),sum(gp[r][0] not in ('const','partial') for r in regs)

def census(trace,admitted,entry,record,section=lambda a,n:'unclassified'):
    _,initial,parent,_,_=entry
    sp=initial[1][1];frame=record[3];allow={x[0] for x in admitted}
    out=[]
    for i,(pc,w,gp,mem) in enumerate(trace[:-1]):
        _,_,after_gp,after=trace[i+1]
        family=boundary_shape(w)
        changed=sum(mem.get(a)!=after.get(a) for a in set(mem)|set(after))
        if family=='load':
            geometry=load_geometry(w,gp)
            if geometry is None:raise ValueError('partial audit load form')
            kind,at,n=geometry
            if kind=='stack':
                region='child' if sp-frame<=at<at+n<=sp else 'caller' if sp<=at<at+n<=sp+704 else 'outside'
                unknown=sum(mem.get(a,('uninitialized',))[0]=='uninitialized' for a in range(at,at+n))
            else:region=section(at,n);unknown=0
            result=after_gp[(w>>21)&31][0]
            out.append((i+1,'load',n,region,unknown,changed,result,int(pc in allow)))
        elif family=='store':
            n,region,prior,inherited,source,aligned=store_location(w,gp,mem,parent,sp,frame,section)
            out.append((i+1,'store',n,region,0,changed,source,int(pc in allow)))
        elif changed:
            out.append((i+1,'other',0,'unknown',0,changed,'none',0))
    _,w,gp,_=trace[-1]
    return tuple(out),integer_shape(w,gp)

def plan(d,e):
    result,extra,trace,admitted,entry,record=replay(d,e,details=True)
    if len(trace)!=12 or len(admitted)!=4:raise ValueError('partial audit predecessor')
    return census(trace,admitted,entry,record,lambda a,n:classify_section(e,a,n))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','partial audit predecessor','partial audit load address','partial audit load form'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():rows,boundary=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_ACCESS_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_ACCESS_AUDIT verified=1 sites={len(rows)} loads={sum(r[1]=="load" for r in rows)} stores={sum(r[1]=="store" for r in rows)} original_execution=0')
    for ordinal,kind,n,region,unknown,changed,source,admitted in rows:
        print(f'FORMATTER_PARTIAL_ACCESS ordinal={ordinal} kind={kind} width={n} region={region} unknown_bytes={unknown} changed_bytes={changed} value_kind={source} admitted_caller={admitted}')
    name,inputs,partial,other=boundary
    print(f'FORMATTER_PARTIAL_NEXT_INTEGER family={name} inputs={inputs} partial_inputs={partial} nonconstant_inputs={other} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
