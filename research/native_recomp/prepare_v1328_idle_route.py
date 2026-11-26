#!/usr/bin/env python3
"""Authenticate native idle selection and install read-only instruction hooks."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v1321_combined_resume import plan,audit,CLEAR,CALLBACK,SELECT
from prepare_v1307_cooperative_fixture import ENABLE,DISABLE,SET
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v1299_reply_return import verify_resume

def install(root,result):
    coop,_,edges,indirect,callback=result
    roots=coop[0];routes={a:roots[a] for a in (ENABLE,SELECT,DISABLE,CLEAR,SET)}
    routes[CALLBACK]=tuple(callback)
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in routes.items() for pc in reachable(a,ws)}
    sources={p:p.read_text() for p in sorted(root.glob('output_*.cpp'))}
    main=(root/'main_output.cpp').read_text()
    n=audit(list(sources.values()),main,result)
    if audit_native(sources.values(),main,expected)!=len(expected):raise ValueError('selection coverage')
    verify_resume(main,((coop[2][0],ENABLE),*((e[1],SELECT) for e in indirect)))
    for target,lr,word,_ in indirect:
        site=lr-4
        pat=re.compile(r'(?mi)^loc_'+f'{site:X}'+r': ;\n(.*?)(?=^loc_[0-9a-f]+: ;|\Z)',re.S|re.M)
        blocks=[m[1] for s in sources.values() for m in pat.finditer(s)]
        if len(blocks)!=1 or 'ctx.pc = ctx.ctr; return;' not in blocks[0] or f'ctx.lr = 0x{lr:X};' not in blocks[0]:
            raise ValueError('selection indirect dispatch')
    seen=set();changes={}
    for path,source in sources.items():
        s=source
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('selection hook identity')
            seen.add(pc);i=hits[0].end();s=s[:i]+f'    v1328_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=source:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('selection hook include')
            changes[path]=s.replace(anchor,anchor+'\nvoid v1328_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(expected):raise ValueError('selection hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'V1328_SELECTION_TRANSLATION verified=1 route_labels={len(expected)} combined_labels={n} indirect_edges={len(indirect)}')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        install(a.out,plan(a.dol.read_bytes(),a.elf.read_bytes()));return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','selection coverage','selection indirect dispatch','selection hook identity','selection hook include','selection hook coverage',
                 'resume coverage','resume direct owner','return dispatch identity','native IPC coverage','native IPC label identity','native IPC label body','native IPC dispatch')
        print('V1328_SELECTION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
