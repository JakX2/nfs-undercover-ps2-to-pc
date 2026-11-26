#!/usr/bin/env python3
"""Private static ACK credit/profiling geometry; no original words exported."""
import argparse
import hashlib
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,OWNER_SHA,EXPECTED_GPRS
from make_private_elf_symbol_map import HEADER,ORIGINAL_SHA256
from make_v1255_ack_fixture import geometry,IPC
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
    rd=(load>>21)&31
    if (sda(load,32,bases)!=address or sda(store,36,bases)!=address or
        add>>26!=14 or (add>>21)&31!=rd or (add>>16)&31!=rd or add&0xffff!=0xffff or
        (store>>21)&31!=rd):raise ValueError('ack profile dataflow')
    return True

def credit_sites(root,words,address,call,bases):
    if not root<call<root+4*len(words):raise ValueError('ack call extent')
    sites=[]
    for i,w in enumerate(words):
        pc=root+4*i
        if pc>=call:break
        if sda(w,36,bases)==address:sites.append(i)
    if len(sites)!=1:raise ValueError('ack credit stores')
    i=sites[0];rs=(words[i]>>21)&31
    # Compiler may interleave control flow, but this narrow geometry
    # accepts only a consecutive load/add/store credit increment.
    if i<2:raise ValueError('ack credit dataflow')
    load,add=words[i-2:i]
    if (sda(load,32,bases)!=address or (load>>21)&31!=rs or add>>26!=14 or
        (add>>21)&31!=rs or (add>>16)&31!=rs or add&0xffff!=1):raise ValueError('ack credit dataflow')
    return len(sites)

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

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    allowed={'size','identity','ack profile extent','ack profile dataflow','ack call extent','ack credit stores',
             'ack credit dataflow','ack profile edge','ack object overlap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        labels,credit,profile=derive(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        print('IPC_DEFERRED_ACK_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'IPC_DEFERRED_ACK_GEOMETRY verified=1 profile_labels={labels} credit_stores={credit} profile_stores={profile}')
    return 0
if __name__=='__main__':raise SystemExit(main())
