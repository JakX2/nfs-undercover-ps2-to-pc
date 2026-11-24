#!/usr/bin/env python3
"""Observe each counted successor after V413 restores the interrupted context.
The raw addresses remain in the owner-private native log, never CI stdout.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from derive_v413_nand_context_resume import PREFIX, TRACE_NEXT, TRIAL, OBSERVE, HEAD

SEAM='    ++v396_calls;'
OBSERVE_NEW=OBSERVE.replace(
    'if(v413_context.observe(ctx,coherent))',
    'if(v413_context.observe(ctx,coherent)){',1).replace(
    '<<v413_context.interrupted<<std::endl;',
    '<<v413_context.interrupted<<std::endl;\n'
    '      if(v413_context.restored()&&v413_context.interrupted==1u)\n'
    '        std::cout<<"V414_RESUMED_BEGIN after="<<v396_calls<<std::endl;\n'
    '    }',1)
TRACE='''
    if(v413_context.restored()&&v413_context.interrupted==1u){
      std::cout<<"V414_RESUMED_ENTRY call="<<v396_calls
               <<" pc="<<std::hex<<addr<<std::dec<<std::endl;
    }'''

def patch(source:str)->str:
    if ('V414_RESUMED_ENTRY' in source or any(source.count(a)!=1 for a in
            (SEAM,HEAD,TRACE_NEXT+PREFIX,TRIAL,OBSERVE, 'V413_CONTEXT_RESTORE regs=',
             'V413_CONTEXT_EXIT calls=', 'V413_CONTEXT_TRIAL complete='))):
        raise ValueError('geometry')
    out=source.replace(SEAM,SEAM+TRACE,1).replace(OBSERVE,OBSERVE_NEW,1)
    if out.replace(SEAM+TRACE,SEAM,1).replace(OBSERVE_NEW,OBSERVE,1)!=source:raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        out=patch(a.prior.read_text(encoding='utf-8'))
        with a.output.open('x',encoding='utf-8') as f:f.write(out)
    except (OSError,ValueError):
        print('V414_COVERAGE_ROUTE installed=0');return 1
    print('V414_COVERAGE_ROUTE installed=1 read_only=1 cap=192');return 0
if __name__=='__main__':raise SystemExit(main())
