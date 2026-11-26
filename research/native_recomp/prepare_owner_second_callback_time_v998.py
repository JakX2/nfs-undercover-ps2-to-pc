#!/usr/bin/env python3
"""Extend the original second-handler callback through its time-helper return."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_second_callback_v994 import plan as base_plan,header as base_header,install,patch_analyzer
from prepare_owner_callback_time_v802 import plan as time_plan
from prepare_v813_callback_time import render

def plan(dol,elf):
    p,shared,C,S,call,full,sites=base_plan(dol,elf)
    q,T,D,U,R,ts,leaves=time_plan(dol,elf)
    tr,c,s,save_site,_,_=q
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    prefix=roots[C][:-1]
    if (c,s)!=(C,S) or len(prefix)!=(save_site-C)//4+2 or list(tr[C][:len(prefix)])!=list(prefix):raise ValueError('callback time prefix')
    for a in (T,D,U,R):
        if a not in roots or list(roots[a])!=list(tr[a]):raise ValueError('callback time shared')
    if list(tr[C][:-1])!=list(full[:len(tr[C])-1]):raise ValueError('callback time identity')
    roots[C]=list(tr[C])
    for a,ws in roots.items():
        if a!=C and a<C+4*len(roots[C]) and C<a+4*len(ws):raise ValueError('callback time overlap')
    extra=(*extra[:-1],(ts,T,4*len(roots[T]),roots[C][(ts-C)//4],roots[T]),extra[-1])
    q=(roots,edges,indirect,iw,hw,dw,guard,extra)
    continuation=roots[C][len(prefix)-1:-1]
    return (q,*p[1:]),shared,C,S,call,full,sites,prefix,render(C,ts,continuation,T,roots[T],leaves)

def header(p,shared,C,S,call,full,sites,prefix,time_header,out):
    base_header(p,shared,C,S,call,full,sites,out)
    text=out.read_text()
    old=next(l for l in text.splitlines() if ' callback_prefix{' in l)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    text=replace_exact(text,old,f'inline constexpr std::array<uint32_t,{len(prefix)}> callback_prefix{{'+fmt(prefix)+'};')
    out.write_text(text+'\n'+time_header.replace('#pragma once\n','',1))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p,shared,C,S,call,full,sites,prefix,time_header=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,call,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(p,shared,C,S,call,full,sites,prefix,time_header,x.output);print('V998_CALLBACK_TIME_GEOMETRY original_indirect=1 shared_time=1 leaf_roots=3 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('callback time prefix','callback time shared','callback time identity','callback time overlap','native coverage','native owner','hook identity')
        print('V998_CALLBACK_TIME_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
