#!/usr/bin/env python3
"""Private static ACK credit/profiling geometry; no original words exported."""
import argparse
import hashlib
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,OWNER_SHA,EXPECTED_GPRS
from make_private_elf_symbol_map import HEADER,ORIGINAL_SHA256
from make_v1255_ack_fixture import geometry,IPC,DISPATCH_RETURN
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_ipc_dispatch_geometry import credit_object
from prepare_ipc_profile_geometry import layout
from prepare_v1414_ipc_ring import ring_object

def sda(w,op,bases):
    if w>>26!=op:return None
    ra=(w>>16)&31
    if ra not in bases:return None
    imm=w&0xffff
    return (bases[ra]+imm-(0x10000 if imm&0x8000 else 0))&0xffffffff

def decrement_leaf(words,address,bases):
    # The leaf must load and decrement the same word, then return;
    # reject additional stores or an unrelated register dataflow.
    if len(words)!=4 or words[-1]!=0x4e800020:raise ValueError('ack profile extent')
    load,add,store,_=words
    rd=(load>>21)&31;result=(add>>21)&31
    if sda(load,32,bases)!=address:raise ValueError('ack profile load')
    if sda(store,36,bases)!=address:raise ValueError('ack profile store')
    if (not rd or add>>26!=14 or (add>>16)&31!=rd or add&0xffff!=0xffff or
        (store>>21)&31!=result):raise ValueError('ack profile dataflow')
    return True

def gpr_def(w):
    op=w>>26;xo=(w>>1)&1023
    if op in (7,8,12,13,14,15,32,34,40,42):return (w>>21)&31
    if op in (20,21,23,24,25,26,27,28,29):return (w>>16)&31
    if op in (10,11,16,36,38,44) and not(op==16 and w&1):return -1
    if op==18 and not(w&1):return -1
    if op==31 and xo in (0,32):return -1
    if op==31 and xo==444:return (w>>16)&31
    return None

def previous_def(words,end,reg,limit):
    for i in range(end-1,max(-1,end-limit-1),-1):
        dest=gpr_def(words[i])
        if dest is None:raise ValueError('ack credit clobber')
        if dest==reg:return i
    raise ValueError('ack credit definition')

def reachable(words,blocked=None):
    seen=set();work=[0]
    while work:
        i=work.pop()
        if i==blocked or i in seen or not 0<=i<len(words):continue
        seen.add(i);w=words[i];op=w>>26;xo=(w>>1)&1023
        if op==19 and xo in (16,50,528):
            if xo==16 and not(w&1) and ((w>>21)&20)!=20:work.append(i+1)
            continue
        if op in (16,18) and not(w&1):
            if w&2:raise ValueError('ack absolute branch')
            mask,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            target=i+(((w&mask)^sign)-sign)//4
            if 0<=target<len(words):work.append(target)
            if op==18 or ((w>>21)&20)==20:continue
        work.append(i+1)
    return seen

def credit_sites(root,words,address,call,bases,*,return_site=False):
    if not root<call<root+4*len(words):raise ValueError('ack call extent')
    sites=[]
    for i,w in enumerate(words):
        pc=root+4*i
        if pc>=call:break
        if sda(w,36,bases)==address:sites.append(i)
    if len(sites)!=1:raise ValueError('ack credit stores')
    i=sites[0];rs=(words[i]>>21)&31
    j=previous_def(words,i,rs,16);add=words[j];rd=(add>>16)&31
    if not rd or add>>26!=14 or (add>>21)&31!=rs or add&0xffff!=1:
        raise ValueError('ack credit add')
    k=previous_def(words,j,rd,16);load=words[k]
    if sda(load,32,bases)!=address or (load>>21)&31!=rd:
        raise ValueError('ack credit load')
    if i not in reachable(words) or i in reachable(words,k) or i in reachable(words,j):
        raise ValueError('ack credit dominance')
    for n in range(k,i):
        w=words[n];op=w>>26
        if op in (16,18) and not(w&1):
            mask,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            if (((w&mask)^sign)-sign)<=0:raise ValueError('ack credit loop')
    return root+4*i if return_site else len(sites)

def derive(d,e):
    if hashlib.sha256(d).hexdigest()!=OWNER_SHA or hashlib.sha256(e).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('identity')
    native,_,edges,_=geometry(d,e)
    candidates=[x for x in edges if x[0] in native and x[0] not in (IPC,0x8051905c,0x8051906c)]
    if len(candidates)!=1:raise ValueError('ack profile edge')
    target,lr,_,_=candidates[0]
    credit=credit_object(d,e);prof=layout(d,e);ring=ring_object(d,e)
    ranges=[credit,*prof,ring[:2]]
    ordered=sorted(ranges)
    if any(a+n>b for (a,n),(b,_) in zip(ordered,ordered[1:])):raise ValueError('ack object overlap')
    bases={i:EXPECTED_GPRS[i] for i in (2,13)}
    decrement_leaf(native[target],prof[1][0],bases)
    credit_sites(IPC,native[IPC],credit[0],lr-4,bases)
    return len(native[target]),1,1

def execution_plan(d,e):
    derive(d,e)
    native,_,edges,_=geometry(d,e)
    read,write=0x8051905c,0x8051906c
    profile=next(x for x in native if x not in (IPC,read,write))
    admitted={IPC,read,write,profile}
    calls=tuple((lr-4,t,w) for t,lr,w,_ in edges if t in admitted)
    if any(t==IPC for _,t,_ in calls):raise ValueError('ack recursive call')
    profile_call=[site for site,t,_ in calls if t==profile]
    if len(profile_call)!=1:raise ValueError('ack profile edge')
    bases={i:EXPECTED_GPRS[i] for i in (2,13)}
    credit=credit_sites(IPC,native[IPC],credit_object(d,e)[0],profile_call[0],bases,return_site=True)
    words={a+4*i:(a,w) for a,ws in native.items() for i,w in enumerate(ws)}
    ret=exact_words(d,e,DISPATCH_RETURN,1)[0]
    return (IPC,DISPATCH_RETURN,ret,IPC+4*(len(native[IPC])-1),read,write,profile,credit,profile+8),words,calls

def render(p):
    expect,words,calls=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    def arr(name,typ,rows):
        return f'inline constexpr std::array<undercover::wii::{typ},{len(rows)}> {name}'+'{'+','.join('undercover::wii::'+typ+'{'+fmt(row)+'}' for row in rows)+'};\n'
    return ('#pragma once\n#include "wii_deferred_ack_execution.h"\nnamespace deferred_ack_private {\n'+
        arr('words','IpcDispatchWord',[(owner,pc,w) for pc,(owner,w) in sorted(words.items())])+
        arr('calls','IpcDispatchEdge',calls)+
        'inline constexpr undercover::wii::DeferredAckExpectation expected{'+fmt(expect)+',words,calls};\n}\n')

def audit_execution(root,p):
    expect,words,calls=p
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,(root/'main_output.cpp').read_text(),words)
    for site,target,_ in calls:
        hits=[s for s in sources if f'loc_{site:X}: ;' in s]
        if len(hits)!=1:raise ValueError('ack native edge')
        verify_direct(hits[0],site,target)
    for pc,(_,w) in words.items():
        hook=f'    v1266_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources)!=1:raise ValueError('ack prior hook')
    print(f'DEFERRED_ACK_TRANSLATION verified=1 labels={len(words)} direct_edges={len(calls)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('--out',type=Path);a.add_argument('--audit',type=Path);q=a.parse_args()
    allowed={'size','identity','ack profile extent','ack profile dataflow','ack profile load','ack profile store','ack call extent','ack credit stores',
             'ack credit dataflow','ack credit clobber','ack credit definition','ack credit add','ack credit load','ack credit dominance','ack credit loop','ack absolute branch','ack profile edge','ack object overlap','ack recursive call','ack native edge','ack prior hook',
             'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        labels,credit,profile=derive(d,e)
        if q.audit:audit_execution(q.audit,execution_plan(d,e));return 0
        if q.out:
            p=execution_plan(d,e)
            with (q.out/'private_deferred_ack_execution.h').open('x') as f:f.write(render(p))
            print(f'DEFERRED_ACK_PRIVATE verified=1 labels={len(p[1])} direct_edges={len(p[2])}')
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        print('IPC_DEFERRED_ACK_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'IPC_DEFERRED_ACK_GEOMETRY verified=1 profile_labels={labels} credit_stores={credit} profile_stores={profile}')
    return 0
if __name__=='__main__':raise SystemExit(main())
