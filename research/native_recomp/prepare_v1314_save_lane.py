#!/usr/bin/env python3
"""Authenticate and install exact save leaf/caller hooks. Private output only."""
import argparse,re,struct
from pathlib import Path
from make_v1256_scheduler_fixture import geometry,SELECT,SAVE
from prepare_v1307_cooperative_fixture import SAVE_RETURN
from prepare_owner_context_v720 import L
from prepare_v419_full_start import MAX_DOL,direct_bl,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from save_provenance_v1312 import audit_save

def plan(dol,elf):
    roots,*_=geometry(dol,elf);ws=tuple(roots[SAVE]);gqr=audit_save(ws)
    i=(SAVE_RETURN-SELECT)//4
    if not gqr or not 1<=i<len(roots[SELECT]) or direct_bl(roots[SELECT][i-1],SAVE_RETURN-4)!=SAVE:
        raise ValueError('save call identity')
    return ws,roots[SELECT][i],gqr

def render(p):
    ws,ret,gqr=p;f=lambda a:f'0x{a:08x}u'
    return '\n'.join(('#pragma once','#include "wii_cooperative_save_lane_v1314.h"','#include <array>','namespace v1314 {',
        f'inline constexpr std::array<uint32_t,{len(ws)}> words'+'{'+','.join(map(f,ws))+'};',
        'inline constexpr undercover::wii::CooperativeSaveLane::Expectation expected(uint32_t thread){return {{thread,'+
        ','.join(map(f,(SAVE,SAVE_RETURN,L,L+53*4,0x800000d4,0x800000c0,0x800000e4,0xffffffff)))+'},words,'+f(ret)+','+str(gqr)+'u};}',
        '}',''))

def install(root,p):
    ws,ret,_=p
    expected={SAVE+4*i:(SAVE,w) for i,w in enumerate(ws)}
    expected[SAVE_RETURN]=(SELECT,ret)
    sources={p:p.read_text() for p in sorted(root.glob('output_*.cpp'))}
    if audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):
        raise ValueError('save native coverage')
    owners=[s for s in sources.values() if f'loc_{SAVE_RETURN-4:X}: ;' in s]
    if len(owners)!=1:raise ValueError('save call identity')
    verify_direct(owners[0],SAVE_RETURN-4,SAVE)
    seen=set();changes={}
    for path,source in sources.items():
        s=source
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('save hook identity')
            seen.add(pc);i=hits[0].end()
            s=s[:i]+f'    v1314_save_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=source:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('save hook include')
            changes[path]=s.replace(anchor,anchor+'\nvoid v1314_save_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(expected):raise ValueError('save hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'V1314_SAVE_TRANSLATION verified=1 native_labels={len(expected)} original_execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        result=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(a.out,result);return 0
        raw=(a.out/'fixture.dol').read_bytes();sizes=symbols((a.out/'symbols.csv').read_text())
        ws,ret,_=result
        if sizes.get(SAVE)!=4*len(ws) or words_at(raw,SAVE,len(ws))!=ws or words_at(raw,SAVE_RETURN,1)!=(ret,):
            raise ValueError('save fixture identity')
        with (a.out/'v1314_private_save.h').open('x') as f:f.write(render(result))
        print('V1314_SAVE_FIXTURE verified=1 additional_roots=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','save call identity','save native coverage','save hook identity','save hook include','save hook coverage','save fixture identity')
        print('V1314_SAVE_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
