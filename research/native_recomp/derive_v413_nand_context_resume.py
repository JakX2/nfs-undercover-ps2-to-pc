#!/usr/bin/env python3
"""Separate 192-call NAND candidate with a read-only OSLoadContext witness."""
from __future__ import annotations
import argparse
from pathlib import Path
from derive_v412_nand_legacy_frontier import RESUME
from derive_v405_nand_second_half import TRACE_NEXT, TRIAL_NEXT, EXIT_OBSERVER

CAPS=(('if(owned||v396_calls==96u){','if(owned||v396_calls==192u){',1),
      ('const bool bounded=!owned&&v396_calls==96u;',
       'const bool bounded=!owned&&v396_calls==192u;',1),
      ('nwii::runtime::v396_calls==96u','nwii::runtime::v396_calls==192u',2),
      ('nwii::runtime::v396_calls<=96u','nwii::runtime::v396_calls<=192u',2))
INCLUDE='#include "wii_nand_y1_exception.h"'
STATE='static unsigned v406_checkpoint_count=0u;'
RESET='nwii::runtime::v405_reported=0u;'
HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
PENDING='bool process_pending_callbacks(CPUContext& ctx){'
EXPECTED='''const unsigned v405_expected=nwii::runtime::v396_calls>48u?
      nwii::runtime::v396_calls-48u:0u;'''
EXPECTED_NEW='''const unsigned v405_expected=nwii::runtime::v396_calls>=96u?48u:
      (nwii::runtime::v396_calls>48u?nwii::runtime::v396_calls-48u:0u);'''
ACTIVE='''v250_candidate_mode&&v250_nand_seen==1u&&v388_active&&
     v389_after_y1&&v389_flag_seen==1u&&v395_next_seen==1u&&
     v400_parent_site==1u&&v396_kind==0u'''
TRACE='''
  // Observe only the authenticated dispatcher OSLoadContext callsite.
  if('''+ACTIVE+'''&&ctx.pc==addr&&addr==0x805229b4u&&ctx.lr==0x80526cbcu){
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    if(v413_context.capture(ctx,v377_resume,v377_srr1,masked))
      std::cout<<"V413_CONTEXT_LOAD mapped="<<v413_context.mapped<<std::endl;
  }
'''
OBSERVE='''
  if('''+ACTIVE+'''){
    using B=undercover::wii::IosBus;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
        (((ctx.msr&B::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    if(v413_context.observe(ctx,coherent))
      std::cout<<"V413_CONTEXT_RESTORE regs="<<v413_context.regs
               <<" msr="<<v413_context.msr<<" coherent="<<v413_context.coherent
               <<" interrupted="<<v413_context.interrupted<<std::endl;
  }
'''
PREFIX='''
    if(v396_calls==96u){
      v413_prefix=unsigned(v405_tail_calls==48u&&v398_site_seen==1u&&
                            v400_parent_site==1u);
      std::cout<<"V413_CONTEXT_PREFIX verified="<<v413_prefix<<std::endl;
    }'''
EXIT='''  std::cout<<"V413_CONTEXT_EXIT calls="<<nwii::runtime::v396_calls
           <<" prefix="<<nwii::runtime::v413_prefix
           <<" load="<<nwii::runtime::v413_context.load
           <<" mapped="<<nwii::runtime::v413_context.mapped
           <<" hit="<<nwii::runtime::v413_context.hit
           <<" restored="<<unsigned(nwii::runtime::v413_context.restored())
           <<" interrupted="<<nwii::runtime::v413_context.interrupted
           <<" matched="<<unsigned(v410_matched_stop)<<std::endl;
'''
TRIAL='''
  const bool v413_complete=v405_completed&&nwii::runtime::v413_prefix==1u&&
      nwii::runtime::v396_calls==192u&&!c.is_running;
  std::cout<<"V413_CONTEXT_TRIAL complete="<<unsigned(v413_complete)<<std::endl;
  check(v413_complete,"V413 bounded NAND context continuation incomplete");'''

def patch(source:str)->str:
    # V412's obsolete V260 frontier is still retired at the original 50th
    # call. Its exact predicate is retained. The V405 49–96 census stays
    # capped at 48 entries, even though this independent process goes on.
    if 'V413_CONTEXT_' in source or source.count(RESUME)!=1:
        raise ValueError('geometry')
    if any(source.count(a)!=1 for a in (INCLUDE,STATE,RESET,HEAD,PENDING,
            TRACE_NEXT,TRIAL_NEXT,EXIT_OBSERVER,EXPECTED)):
        raise ValueError('geometry')
    pairs=list(CAPS)+[(INCLUDE,INCLUDE+'\n#include "wii_v413_context_witness.h"',1),
        (STATE,STATE+'\nstatic undercover::wii::NandContextWitness v413_context{};\nstatic unsigned v413_prefix=0u;',1),
        (RESET,RESET+'\n  nwii::runtime::v413_context={};\n  nwii::runtime::v413_prefix=0u;',1),
        (HEAD,HEAD+TRACE,1),(PENDING,PENDING+OBSERVE,1),
        (TRACE_NEXT,TRACE_NEXT+PREFIX,1),
        (EXPECTED,EXPECTED_NEW,1),
        ('  check(v390_completed,\n        "V390 original NAND guest never left Hollywood ACK for next callee");',
         EXIT+'  check(v390_completed,\n        "V390 original NAND guest never left Hollywood ACK for next callee");',1),
        ('  check(v405_completed,"V405 original guest post-48 call census incomplete");',
         '  check(v405_completed,"V405 original guest post-48 call census incomplete");'+TRIAL,1)]
    out=source
    for old,new,count in pairs:
        if out.count(old)!=count:raise ValueError('seam')
        out=out.replace(old,new)
    back=out
    for old,new,count in reversed(pairs):
        if back.count(new)!=count:raise ValueError('route')
        back=back.replace(new,old)
    if back!=source or out.count(RESUME)!=1:raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        out=patch(a.prior.read_text(encoding='utf-8'))
        with a.output.open('x',encoding='utf-8') as f:f.write(out)
    except (ValueError,OSError):
        print('V413_CONTEXT_ROUTE installed=0');return 1
    print('V413_CONTEXT_ROUTE installed=1 cap=192 prefix96=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
