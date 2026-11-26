#!/usr/bin/env python3
"""Authenticate the actual second IOS_Open return seam without executing STM tail."""
import argparse,struct,re
from pathlib import Path
from prepare_v1337_open_completion import plan,rebuild,ensure_resume,STM,SECOND,OPEN,BLR
from prepare_v629_stm_open import geometry as stm_geometry
from prepare_v1358_open_return import geometry as return_geometry
from prepare_v1281_reply_fixture import symbols
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from make_v1243_stm_fixture import seed_data

def extend(blocks,prefix,body):
    if len(prefix)!=33 or len(body)<=34 or tuple(body[:33])!=tuple(prefix) or blocks.get(STM)!=tuple(prefix)+(BLR,):
        raise ValueError('second return predecessor')
    out={**blocks,STM:tuple(body[:34])+(BLR,)}
    spans=sorted((a,a+4*len(ws)) for a,ws in out.items())
    if any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('second return ownership')
    return out

def scope(prior):
    out=dict(prior)
    if STM in out and out[STM]!=96:raise ValueError('second return ownership')
    out[STM]=140
    spans=sorted(out.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('second return ownership')
    return spans

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--analyzer',action='store_true')
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        p=plan(d,e);shared,_,_,prefix,*_=p;_,body,_,_,paths,_=stm_geometry(d,e)
        body=tuple(body);resume=SECOND+4
        if len(prefix)!=33 or tuple(body[:33])!=prefix or direct_bl(prefix[-1],SECOND)!=OPEN or resume!=STM+33*4:
            raise ValueError('second return geometry')
        w=body[33]
        # Admit one original non-control instruction as the resume label.
        # The next synthetic terminator is never executed by this mode.
        if w>>26 in (16,17,18) or (w>>26==19 and (w>>1)&1023 in (16,50,528)) or (w>>26==31 and (w>>1)&1023==146):
            raise ValueError('second return geometry')
        if seed_data(d,body[:34],paths)!=seed_data(d,prefix,paths):raise ValueError('second return data')
        if q.analyzer:
            if q.symbols is None:raise ValueError('second return extent')
            sizes=symbols(q.symbols.read_text())
            if sizes.get(STM)!=140:raise ValueError('second return extent')
            q.out.write_text(analyzer(q.out.read_text(),scope(combined_scope(d,e,{**sizes,STM:96}))))
            print('V1379_SECOND_ANALYZER verified=1 stm_original_words=34');return 0
        if q.install:
            sources=[f.read_text() for f in sorted(q.out.glob('output_*.cpp'))]
            main_path=q.out/'main_output.cpp';main=main_path.read_text()
            audit_native(sources,main,{SECOND:(STM,prefix[-1]),resume:(STM,w)})
            owners=[s for s in sources if f'loc_{SECOND:X}: ;' in s]
            if len(owners)!=1:raise ValueError('second return owner')
            verify_direct(owners[0],SECOND,OPEN)
            main,added=ensure_resume(main,exact_function(owners[0],STM),STM,resume)
            if added:main_path.write_text(main)
            print(f'V1379_SECOND_TRANSLATION verified=1 native_resume=1 direct_edge=1 resume_added={int(added)}');return 0
        image=q.out/'fixture.dol';csv=q.out/'symbols.csv';raw=image.read_bytes();sizes=symbols(csv.read_text())
        blocks={a:words_at(raw,a,n//4) for a,n in sizes.items()}
        expanded=extend(blocks,prefix,body)
        image.write_bytes(rebuild(raw,expanded))
        csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
        fr,sr,_,_,sc,_=return_geometry(p)
        fmt=lambda v:f'0x{v:08x}u'
        h='#pragma once\n#include "v1358_private_open_return.h"\nnamespace v1379 {\n'
        h+='inline constexpr undercover::wii::OpenReturnExpectation expected{'+','.join(map(fmt,(OPEN,v1358_submit(p),fr,sr,resume,prefix[-1],sc,w)))+',v1358::words};\n}\n'
        with (q.out/'v1379_private_second_return.h').open('x') as f:f.write(h)
        print('V1379_SECOND_FIXTURE verified=1 stm_original_words=34 additional_roots=0');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','second return predecessor','second return ownership','second return geometry','second return data','second return extent','second return owner',
            'completion local resume','completion outer resume','completion root dispatch','completion roundtrip','native IPC duplicate root',
            'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper exact root','helper call label','helper direct native call','helper native return edge'}
        print('V1379_SECOND_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
def v1358_submit(p):
    # The exact authenticated direct Open -> submit edge.
    return p[1][5][0]
if __name__=='__main__':raise SystemExit(main())
