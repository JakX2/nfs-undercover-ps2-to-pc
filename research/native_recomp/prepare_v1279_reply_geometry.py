#!/usr/bin/env python3
"""Private DOL/ELF reply processor geometry, not guest execution.

Only independently authored metadata is printed. Optional header stays
private in the caller's runner. The wake routine remains an entry guard.
"""
import argparse,struct
from pathlib import Path
from prepare_v1266_joined_ack import geometry as prior,IPC
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v626_ipc_fixture import backward_polls
from audit_handler_suffix_v728 import target
REPLY=0x805190c0
READ=0x8051905c
WRITE=0x8051906c
CACHE=0x80522294
WAKE=0x8052a51c
REPLY_LR=0x80519354
WAKE_LR=0x805192d4
BLR=0x4e800020
# V80 owner-verified synchronous reply path admitted these dependencies.
# The callback/free path remains guarded in this narrower fixture.
GUARDS=(0x80522af4,0x805228cc,0x8051ad3c,0x8051b070,WAKE)
ALLOWED=(READ,WRITE,CACHE,*GUARDS)

def shape(body,cache):
    if len(body)!=0x258//4 or body[-1]!=BLR or not 1<=len(cache)<=64 or cache[-1]!=BLR:
        raise ValueError('reply extent')
    edges=[];guard_sites=[]
    for i,w in enumerate(body):
        pc=REPLY+4*i;op=w>>26;xo=(w>>1)&1023
        if op==18 and w&1:
            if w&2:raise ValueError('absolute call')
            dst=direct_bl(w,pc)
            if dst not in ALLOWED:raise ValueError('unknown reply dependency')
            edges.append((pc,dst))
            if dst in GUARDS:guard_sites.append(pc)
        elif op in (16,18):
            if w&3 or not REPLY<=target(pc,w)<REPLY+4*len(body):
                raise ValueError('reply branch closure')
        elif op==17 or (op==19 and xo in (528,50)):
            # Callback/exception instructions are never executed in this
            # synchronous-only lane. Exact original words stay private.
            guard_sites.append(pc)
    pairs=set(edges)
    required={(0x805190e4,READ),(0x805190f8,READ),(0x80519108,WRITE),(WAKE_LR-4,WAKE)}
    if not required<=pairs or not any(dst==CACHE for _,dst in edges):
        raise ValueError('reply required edges')
    if sum(dst==WAKE for _,dst in edges)!=1:raise ValueError('wake edge')
    dcbi=[]
    for i,w in enumerate(cache):
        pc=CACHE+4*i;op=w>>26;xo=(w>>1)&1023
        if op==31 and xo==470:dcbi.append(pc)
        if op in (16,18):
            if w&3 or not CACHE<=target(pc,w)<CACHE+4*len(cache):
                raise ValueError('cache branch closure')
        elif op==17 or (op==19 and xo in (528,50)):
            raise ValueError('cache control')
    if not dcbi:raise ValueError('cache invalidate opcode')
    return tuple(edges),tuple(sorted(set(guard_sites))),tuple(dcbi)

def plan(dol,elf):
    _,native,stop,handler_edges,_,_=prior(dol,elf)
    if sum(a==REPLY and lr==REPLY_LR for a,lr,_,_ in handler_edges)!=1 or REPLY not in stop or WAKE not in stop:
        raise ValueError('reply predecessor')
    sizes=parse_functions(elf)
    if sizes.get(REPLY)!=0x258 or not 4<=sizes.get(CACHE,0)<=256 or sizes[CACHE]&3:
        raise ValueError('reply extent')
    body=exact_words(dol,elf,REPLY,sizes[REPLY]//4)
    cache=exact_words(dol,elf,CACHE,sizes[CACHE]//4)
    if body[0]!=stop[REPLY][0]:raise ValueError('reply predecessor')
    edges,guard_sites,dcbi=shape(body,cache)
    rows=[]
    guards={}
    for site,dst in edges:
        if not sizes.get(dst):raise ValueError('reply symbol')
        entry=exact_words(dol,elf,dst,1)[0]
        if dst in (READ,WRITE) and native[dst][0]!=entry:
            raise ValueError('reply shared leaf')
        if dst in GUARDS:guards[dst]=(entry,)
        rows.append((dst,site+4,body[(site-REPLY)//4],entry))
    if guards[WAKE]!=tuple(stop[WAKE]):raise ValueError('reply predecessor')
    return {REPLY:body,CACHE:cache},guards,tuple(rows),guard_sites,dcbi

def render(p):
    native,guards,rows,guard_sites,dcbi=p
    f=lambda n:f'0x{n:08x}u'
    words={pc+4*i:w for pc,ws in {**native,**guards}.items() for i,w in enumerate(ws)}
    lines=['#pragma once','#include "wii_exception_vector_witness_v457.h"','#include <array>','namespace v1279 {']
    def array(name,kind,items):
        lines.append('inline constexpr std::array<'+kind+','+str(len(items))+'> '+name+'{'+','.join(items)+'};')
    array('edges','undercover::wii::VectorEdge',[
        'undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in rows])
    lines.append('struct Word{uint32_t pc,word;};')
    array('words','Word',['Word{'+f(a)+','+f(w)+'}' for a,w in sorted(words.items())])
    array('guard_sites','uint32_t',list(map(f,guard_sites)))
    array('dcbi_sites','uint32_t',list(map(f,dcbi)))
    array('polls','uint32_t',list(map(f,backward_polls(native))))
    lines.extend(('}',''))
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path)
    p.add_argument('--private-header',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        result=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.private_header:
            with a.private_header.open('x') as out:out.write(render(result))
    except (OSError,ValueError,KeyError,IndexError,struct.error) as e:
        allowed=('reply extent','absolute call','unknown reply dependency','reply branch closure','reply required edges',
                 'wake edge','cache branch closure','cache control','cache invalidate opcode','reply predecessor',
                 'reply symbol','reply shared leaf','size','poll geometry')
        reason=str(e) if str(e) in allowed else 'other'
        print('V1279_REPLY_GEOMETRY accepted=0 reason='+reason.replace(' ','_'));return 1
    print(f'V1279_REPLY_GEOMETRY accepted=1 original_roots=2 direct_edges={len(result[2])} guarded_sites={len(result[3])} dcbi_sites={len(result[4])} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
