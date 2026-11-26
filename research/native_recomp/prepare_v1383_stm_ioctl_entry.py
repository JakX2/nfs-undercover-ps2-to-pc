#!/usr/bin/env python3
"""Private full STM function and guarded original IOS_Ioctl entry."""
import argparse,struct
from pathlib import Path
from prepare_v1379_second_return import STM,SECOND,BLR,scope as prior_scope
from prepare_v1337_open_completion import plan,rebuild,hook_submit
from prepare_v629_stm_open import geometry
from prepare_v1377_stm_tail import scan
from make_start_to_stm_v70 import STM_SIZE,EDGES,IOCTL
from make_v1243_stm_fixture import seed_data
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from make_v624_ipc_geometry import exact_words
from prepare_v1281_reply_fixture import symbols
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_owner_scheduler_v722 import reachable
DISABLE=0x805265ac
CALL=next(pc for pc,dst in EDGES if dst==IOCTL)
DISABLE_CALL=next(pc for pc,dst in EDGES if pc>SECOND and dst==DISABLE)

def text_ranges(d):
    rows=[]
    for i in range(7):
        off,a,n=(struct.unpack_from('>I',d,k+4*i)[0] for k in (0,0x48,0x90))
        if not n:continue
        if off<256 or off+n>len(d) or not 0x80000000<=a<a+n<=0x81800000 or a&3 or n&3:
            raise ValueError('ioctl text')
        rows.append((a,n))
    rows.sort()
    if not rows or any(a+n>b for (a,n),(b,_) in zip(rows,rows[1:])):raise ValueError('ioctl text')
    return tuple(rows)

def extend(blocks,body,ioctl,disable):
    if len(body)*4!=STM_SIZE or blocks.get(STM)!=tuple(body[:34])+(BLR,) or IOCTL in blocks or blocks.get(DISABLE)!=tuple(disable):
        raise ValueError('ioctl predecessor')
    out={**blocks,STM:tuple(body),IOCTL:(ioctl,BLR)}
    spans=sorted((a,a+4*len(ws)) for a,ws in out.items())
    if len(out)+2>49 or any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('ioctl ownership')
    return out

def scope(prior):
    out=dict(prior_scope(prior))
    if IOCTL in out:raise ValueError('ioctl ownership')
    out[STM]=STM_SIZE;out[IOCTL]=8
    spans=sorted(out.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('ioctl ownership')
    return spans

def private_plan(d,e):
    _,body,_,_,paths,_=geometry(d,e);body=tuple(body)
    p=plan(d,e);disable=p[0][DISABLE]
    ioctl=exact_words(d,e,IOCTL,1)[0]
    seen,calls,_,stores,_=scan(STM,body,SECOND+4,{pc:dst for pc,dst in EDGES if pc>SECOND})
    sites=tuple(sorted(pc for pc in stores if pc<=CALL))
    if not sites or len(sites)>8 or any(body[(pc-STM)//4]>>26!=36 or (body[(pc-STM)//4]>>16)&31 not in (2,13) for pc in sites):
        raise ValueError('ioctl store geometry')
    if seed_data(d,body,paths)!=seed_data(d,body[:34],paths):raise ValueError('ioctl data')
    if (CALL,IOCTL) not in calls or (DISABLE_CALL,DISABLE) not in calls:raise ValueError('ioctl call')
    return body,ioctl,disable,seen,sites,text_ranges(d)

def render(p):
    body,ioctl,disable,seen,stores,text=p
    f=lambda v:f'0x{v:08x}u'
    rows=[(STM,pc,body[(pc-STM)//4]) for pc in sorted(seen)]
    rows.extend((DISABLE,pc,disable[(pc-DISABLE)//4]) for pc in sorted(reachable(DISABLE,disable)))
    rows.append((IOCTL,IOCTL,ioctl))
    def arr(name,typ,items):
        return f'inline constexpr std::array<{typ},{len(items)}> {name}'+'{'+','.join(typ+'{'+','.join(map(f,x))+'}' for x in items)+'};\n'
    def edge(site,dst,entry):
        return 'undercover::wii::VectorEdge{'+','.join(map(f,(dst,site+4,body[(site-STM)//4],entry)))+'}'
    return ('#pragma once\n#include "wii_stm_ioctl_entry.h"\nnamespace v1383 {\n'+
        arr('words','undercover::wii::ReplyNativeWord',rows)+
        'inline constexpr std::array<uint32_t,'+str(len(stores))+'> stores{'+','.join(map(f,stores))+'};\n'+
        arr('text','undercover::wii::AllocatorRange',text)+
        'inline constexpr undercover::wii::StmIoctlEntryExpectation expected{'+','.join(map(f,(STM,SECOND+4,CALL)))+','+
        edge(DISABLE_CALL,DISABLE,disable[0])+','+edge(CALL,IOCTL,ioctl)+',words,stores,text};\n}\n')

def install(root,p):
    body,ioctl,disable,seen,_,_=p
    expected={pc:(STM,body[(pc-STM)//4]) for pc in seen}
    expected.update({pc:(DISABLE,disable[(pc-DISABLE)//4]) for pc in reachable(DISABLE,disable)})
    expected[IOCTL]=(IOCTL,ioctl)
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)
    for site,dst in ((DISABLE_CALL,DISABLE),(CALL,IOCTL)):
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('ioctl call owner')
        verify_direct(owners[0],site,dst)
    for pc in reachable(DISABLE,disable):
        w=disable[(pc-DISABLE)//4]
        if sum(s.count(f'    v1270_before(ctx,0x{pc:08x}u,0x{w:08x}u);') for s in sources.values())!=1:
            raise ValueError('ioctl disable hook')
    wanted={pc:body[(pc-STM)//4] for pc in seen if pc<=CALL}
    done=set();changed={}
    for path,s in sources.items():
        prev=s
        for pc,w in wanted.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in done:raise ValueError('ioctl hook')
            done.add(pc)
        if s!=prev:
            anchor='#include "runtime/cpu_context.h"';decl='void v1344_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);'
            if s.count(anchor)!=1 or s.count(decl)>1:raise ValueError('ioctl hook')
            changed[path]=s if decl in s else s.replace(anchor,anchor+'\n'+decl)
    if done!=set(wanted):raise ValueError('ioctl hook')
    for path,s in changed.items():path.write_text(s)
    print(f'V1383_IOCTL_TRANSLATION verified=1 original_labels={len(expected)} stm_hooks={len(wanted)} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--analyzer',action='store_true')
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=private_plan(d,e)
        if q.install:install(q.out,p);return 0
        if q.analyzer:
            if q.symbols is None:raise ValueError('ioctl extent')
            sizes=symbols(q.symbols.read_text())
            if sizes.get(STM)!=STM_SIZE or sizes.get(IOCTL)!=8:raise ValueError('ioctl extent')
            q.out.write_text(analyzer(q.out.read_text(),scope(combined_scope(d,e,{a:(96 if a==STM else n) for a,n in sizes.items() if a!=IOCTL}))))
            print('V1383_IOCTL_ANALYZER verified=1 full_stm=1 guarded_ioctl=1');return 0
        image=q.out/'fixture.dol';csv=q.out/'symbols.csv';raw=image.read_bytes()
        blocks={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
        expanded=extend(blocks,*p[:3]);image.write_bytes(rebuild(raw,expanded,max_roots=49))
        csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
        with (q.out/'v1383_private_stm_ioctl.h').open('x') as f:f.write(render(p))
        print(f'V1383_IOCTL_FIXTURE verified=1 full_stm=1 guarded_ioctl=1 store_sites={len(p[4])} additional_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','ioctl text','ioctl predecessor','ioctl ownership','ioctl store geometry','ioctl data','ioctl call','ioctl call owner',
            'ioctl disable hook','ioctl hook','ioctl extent','completion hook label','completion roundtrip','fixture geometry','fixture range','fixture overlap',
            'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
        print('V1383_IOCTL_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
