#!/usr/bin/env python3
"""Conservative, bounded static census; no original code or private addresses emitted."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,TIME,DISABLE,RESTORE,SCHED
from make_private_elf_symbol_map import parse_functions
from si_second_geometry_v688 import second_plan
from si_nested_geometry_v693 import nested_plan
from audit_si_nested_v690 import target
MASK=0xffffffff
def signed(x):return (x^0x8000)-0x8000
def call_kind(w):
    op=w>>26;xo=(w>>1)&1023
    if not w&1:return 0
    return 1 if op in (16,18) else 2 if op==19 and xo in (16,528) else 0
def region(a):
    if a is None:return 'unknown'
    p=a&0x3fffffff
    if (a&0xc0000000)!=0x40000000 and 0x0d006400<=(p&~0x00800000)<0x0d006500:
        o=(p&~0x00800000)-0x0d006400
        return 'si_control' if o==0x34 else 'si_status' if o==0x38 else 'si_buffer' if 0x80<=o<0x100 else 'si_other'
    if 0x0c000000<=p<0x0c010000 or 0x0d000000<=p<0x0d010000 or 0x0d800000<=p<0x0d810000:return 'other_mmio'
    return 'memory'
def step(w,regs):
    """Track only an explicit whitelist. Unknown instructions forget all constants."""
    op=w>>26;rd=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;imm=w&0xffff
    q=list(regs);access=None
    if op in (14,15):
        base=regs[ra] if ra else 0
        q[rd]=None if base is None else (base+(signed(imm)<<(16 if op==15 else 0)))&MASK
    elif op in (24,25,26,27,28,29):
        v=regs[rd];k=imm<<(16 if op in (25,27,29) else 0)
        q[ra]=None if v is None else ((v|k) if op in (24,25) else (v^k) if op in (26,27) else (v&k))&MASK
    elif 32<=op<=45 or op in (46,47,48,49,50,51,52,53,54,55):
        base=regs[ra] if ra else 0
        addr=None if base is None else (base+signed(imm))&MASK
        write=op in (36,37,38,39,44,45,47,52,53,54,55)
        access=('write' if write else 'read',region(addr))
        if op in (33,35,37,39,41,43,45,49,51,53,55):q[ra]=addr
        if op in (32,33,34,35,40,41,42,43):q[rd]=None
        if op==46:
            for i in range(rd,32):q[i]=None
    elif op==31 and (w>>1)&1023 in (23,55,87,119,279,311,343,375,151,183,215,247,407,439,534,662,790,918):
        xo=(w>>1)&1023
        base=regs[ra] if ra else 0;index=regs[rb]
        addr=None if base is None or index is None else (base+index)&MASK
        write=xo in (151,183,215,247,407,439,662,918)
        access=('write' if write else 'read',region(addr))
        if xo in (55,119,311,375,183,247,439):q[ra]=addr
        if not write:q[rd]=None
    elif op==31 and (w>>1)&1023==444:
        a,b=regs[rd],regs[rb];q[ra]=None if a is None or b is None else a|b
    elif op in (10,11,16,18) or w==0x60000000:pass
    else:q=[None]*32
    return tuple(q),access
def census(root,words):
    if root&3 or not 1<=len(words)<=1024:raise ValueError('extent')
    end=root+4*len(words);states={root:(None,)*32};work=[root]
    accesses={};visits=0;calls=[root+4*i for i,w in enumerate(words) if call_kind(w)];first=set()
    while work:
        pc=work.pop();visits+=1
        if visits>65536:raise ValueError('worklist bound')
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        q,access=step(w,states[pc]);accesses[pc]=access
        if call_kind(w):first.add(calls.index(pc)+1);continue
        if op==17 or op==19 and xo in (16,50,528) or op==31 and xo==146:continue
        dest=[pc+4]
        if op in (16,18):dest=[target(pc,w)]+([pc+4] if op==16 else [])
        for a in dest:
            if a&3 or not root<=a<end:continue
            old=states.get(a);new=q if old is None else tuple(x if x==y else None for x,y in zip(old,q))
            if old!=new:states[a]=new;work.append(a)
    result={k:0 for k in ('read_unknown','write_unknown','read_si_control','write_si_control','read_si_status','write_si_status','read_si_buffer','write_si_buffer','read_si_other','write_si_other','read_other_mmio','write_other_mmio','read_memory','write_memory')}
    for v in accesses.values():
        if v:result['_'.join(v)]+=1
    return result,tuple(sorted(first))
def classify(dol,elf):
    sizes=parse_functions(elf);_,second,_,_,sw=second_plan(dol,elf);_,nested,_,_,nw=nested_plan(dol,elf)
    result=[]
    for lane,root,words in ((2,second,sw),(3,nested,nw)):
        counts,first=census(root,words);result.append(('V695_MMIO_PREFIX',dict(lane=lane,first_calls=len(first),**counts)))
        for i,(pc,w) in enumerate(((root+4*i,w) for i,w in enumerate(words) if call_kind(w)),1):
            k=call_kind(w);row=dict(lane=lane,ordinal=i,kind=k,first=int(i in first),exact=0,words=0,calls=0,returns=0,disable=0,restore=0,time=0,sched=0,same_nested=0)
            if k==1:
                a=target(pc,w);size=sizes.get(a,0);row.update(disable=int(a==DISABLE),restore=int(a==RESTORE),time=int(a==TIME),sched=int(a==SCHED),same_nested=int(a==nested))
                if 0<size<=4096 and size%4==0:
                    code=exact(dol,elf,a,size//4);row.update(exact=1,words=len(code),calls=sum(bool(call_kind(x)) for x in code),returns=code.count(0x4e800020))
            result.append(('V695_CALL_EDGE',row))
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        rows=classify(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):print('V695_DEEP_CENSUS inspected=0');return 1
    for name,row in rows:print(name+' inspected=1 '+' '.join(f'{k}={v}' for k,v in row.items()))
    return 0
if __name__=='__main__':raise SystemExit(main())
