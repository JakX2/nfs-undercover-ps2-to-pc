#!/usr/bin/env python3
"""Extend the authenticated V1383 fixture with full original ioctl and compiler leaves."""
import argparse,struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES,SIZE,BLR
from prepare_v1383_stm_ioctl_entry import scope as prior_scope,STM,STM_SIZE
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v1281_reply_fixture import symbols
from prepare_v419_full_start import MAX_DOL,words_at
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
SAVE_CALL,SAVE=EDGES[0];ALLOC_CALL,ALLOC=EDGES[1];RESTORE=EDGES[-1][1]

def merge(blocks,roots):
    if set(roots)!={IOCTL,SAVE,RESTORE} or len(roots[IOCTL])*4!=SIZE or any(not roots[x] for x in roots):
        raise ValueError('prefix roots')
    if blocks.get(IOCTL)!=(roots[IOCTL][0],BLR) or SAVE in blocks or RESTORE in blocks:
        raise ValueError('prefix predecessor')
    out={**blocks,**roots};check_spans({a:4*len(w) for a,w in out.items()})
    if len(out)+2>51:raise ValueError('prefix cap')
    return out

def check_spans(sizes):
    spans=sorted(sizes.items())
    if any(a&3 or n<=0 or n&3 for a,n in spans) or any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):
        raise ValueError('prefix ownership')
    return spans

def scope(d,e,sizes,roots):
    if any(sizes.get(a)!=4*len(w) for a,w in roots.items()) or sizes.get(STM)!=STM_SIZE:
        raise ValueError('prefix extent')
    old={a:(96 if a==STM else n) for a,n in sizes.items() if a not in roots}
    prior=dict(prior_scope(combined_scope(d,e,old)))
    if prior.get(IOCTL)!=8 or SAVE in prior or RESTORE in prior:raise ValueError('prefix predecessor')
    return check_spans({**prior,**{a:4*len(w) for a,w in roots.items()}})

def render(roots,alloc_word,count):
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=[(a,a+4*i,w) for a,ws in roots.items() for i,w in enumerate(ws)]+[(ALLOC,ALLOC,alloc_word)]
    return ('#pragma once\n#include "wii_ioctl_prefix_v1386.h"\nnamespace v1386 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(rows))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt(row)+'}' for row in rows)+'};\n'
      'inline constexpr undercover::wii::IoctlPrefixExpectation expected{'+
      fmt((IOCTL,SAVE_CALL,SAVE,ALLOC_CALL,ALLOC,count))+',words};\n}\n')

def install(root,roots):
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)
    for site,dst in EDGES:
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('prefix call owner')
        verify_direct(owners[0],site,dst)
    wanted={a:w for a,(owner,w) in expected.items() if owner==SAVE or (owner==IOCTL and a<=ALLOC_CALL)}
    done=set();changed={}
    for path,s in sources.items():
        prev=s
        for pc,w in wanted.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in done:raise ValueError('prefix hook')
            done.add(pc)
            old=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if s.count(old)!=1:raise ValueError('prefix hook')
            s=s.replace(old,old.replace('v1344_before','v1386_before'))
        if s!=prev:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('prefix include')
            changed[path]=s.replace(anchor,anchor+'\nvoid v1386_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(wanted):raise ValueError('prefix hook coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'V1386_IOCTL_TRANSLATION verified=1 labels={len(expected)} direct_edges=6 prefix_hooks={len(done)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--analyzer',action='store_true')
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();roots,_,_,_,_,save,*_=plan(d,e)
        if q.install:install(q.out,roots);return 0
        if q.analyzer:
            if q.symbols is None:raise ValueError('prefix extent')
            q.out.write_text(analyzer(q.out.read_text(),scope(d,e,symbols(q.symbols.read_text()),roots)))
            print('V1386_IOCTL_ANALYZER verified=1 full_wrapper=1 compiler_roots=2');return 0
        image=q.out/'fixture.dol';csv=q.out/'symbols.csv';raw=image.read_bytes()
        blocks={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
        expanded=merge(blocks,roots);new=rebuild(raw,expanded,max_roots=51)
        header=render(roots,exact_words(d,e,ALLOC,1)[0],save[1])
        with (q.out/'v1386_private_ioctl_prefix.h').open('x') as f:f.write(header)
        image.write_bytes(new)
        csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
        print('V1386_IOCTL_FIXTURE verified=1 wrapper_words=78 added_roots=2');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','prefix roots','prefix predecessor','prefix cap','prefix ownership','prefix extent',
          'prefix call owner','prefix hook','prefix include','prefix hook coverage','fixture geometry','fixture range','fixture overlap',
          'completion roundtrip','completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body',
          'native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
        print('V1386_IOCTL_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
