#!/usr/bin/env python3
"""V405: observe calls 49–96 of a SEPARATE original-Wii AOT candidate.

Preserves the authenticated V403 24-call and V402 48-call native binaries,
and the independent V404 96-call candidate. This adds only counters and
fixed-format owner-private events to another 96-call binary. No changed PPC,
PC/LR/CTR, memory, IOS, NAND reply, or native return routing.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

STATE='static unsigned v403_return_sp=0u,v403_family=0u,v403_reported=0u;'
RESET='nwii::runtime::v403_reported=0u;'
TRACE='    v397_origin_mask|=(1u<<(v397_class-1u));'
STOP='''               <<" parent_return="<<v400_parent_site<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v404_completed,"V402 extended original guest frontier incomplete");'''
MARKER='V405_NAND_SECOND_HALF tail_calls='
TRIAL_MARKER='V405_NAND_SECOND_TRIAL tail_calls='
CHECKPOINT='V406_NAND_CHECKPOINT call='
EXIT_MARKER='V410_NAND_GUEST_RUN_EXIT calls='
EXIT_CHECK='''  check(v390_completed,
        "V390 original NAND guest never left Hollywood ACK for next callee");'''
EXIT_OBSERVER=r'''  // The 96-call candidate may finish running without an observer stop.
  // Capture sanitized final CPU state BEFORE the unchanged legacy V390
  // posttrial assertion. This does not override a guest register or failure.
  const bool v410_matched_stop=nwii::runtime::v396_kind!=0u&&
      nwii::runtime::v396_stop_pc==c.pc&&nwii::runtime::v396_stop_lr==c.lr;
  std::cout<<"V410_NAND_GUEST_RUN_EXIT calls="<<nwii::runtime::v396_calls
           <<" kind="<<nwii::runtime::v396_kind
           <<" running="<<unsigned(c.is_running)
           <<" mapped="<<unsigned(c.mmu.get_ptr(c.pc)!=nullptr)
           <<" matched_stop="<<unsigned(v410_matched_stop)
           <<" v390="<<unsigned(v390_completed)<<std::endl;
  check(v390_completed,
        "V390 original NAND guest never left Hollywood ACK for next callee");'''
STATE_NEXT=STATE+'''
static unsigned v405_tail_calls=0u,v405_selected=0u;
static unsigned v405_isfs=0u,v405_parent=0u,v405_other=0u;
static unsigned v405_nand=0u,v405_cache=0u,v405_reported=0u;
// This single-process checkpoint budget is deliberately NOT reset per trial.
static unsigned v406_checkpoint_count=0u;'''
RESET_NEXT=RESET+'''
  nwii::runtime::v405_tail_calls=0u;
  nwii::runtime::v405_selected=0u;
  nwii::runtime::v405_isfs=0u;
  nwii::runtime::v405_parent=0u;
  nwii::runtime::v405_other=0u;
  nwii::runtime::v405_nand=0u;
  nwii::runtime::v405_cache=0u;
  nwii::runtime::v405_reported=0u;'''
TRACE_NEXT=TRACE+r'''
    // Original guest calls only, in the independent 96-call process.
    // Callsite origin is a *region* classifier, not proof of a BLR.
    if(v396_calls>48u&&v396_calls<=96u){
      ++v405_tail_calls;
      if(v397_class==1u)++v405_selected;
      else if(v397_class==2u)++v405_isfs;
      else if(v397_class==3u)++v405_parent;
      else ++v405_other;
      if(addr==0x8051e06cu)++v405_nand;
      if(addr==0x80522294u)++v405_cache;
      // At most 48 original guest entries logged across the entire process,
      // even if a later native assertion aborts before V404's stop record.
      if(v406_checkpoint_count<48u){
        ++v406_checkpoint_count;
        std::cout<<"V406_NAND_CHECKPOINT call="<<v396_calls
                 <<" origin="<<v397_class
                 <<" selected="<<v398_site_seen
                 <<" parent="<<v400_parent_site<<std::endl;
      }
    }'''
STOP_NEXT=r'''               <<" parent_return="<<v400_parent_site<<std::endl;
      v405_reported=1u;
      std::cout<<"V405_NAND_SECOND_HALF tail_calls="<<v405_tail_calls
               <<" selected="<<v405_selected
               <<" isfs="<<v405_isfs
               <<" parent="<<v405_parent
               <<" other="<<v405_other
               <<" nand="<<v405_nand
               <<" cache="<<v405_cache<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_NEXT=r'''  check(v404_completed,"V402 extended original guest frontier incomplete");
  const unsigned v405_expected=nwii::runtime::v396_calls>48u?
      nwii::runtime::v396_calls-48u:0u;
  const bool v405_completed=v404_completed&&
      nwii::runtime::v405_reported==1u&&
      nwii::runtime::v405_tail_calls<=48u&&
      nwii::runtime::v405_tail_calls==v405_expected&&
      nwii::runtime::v405_selected+nwii::runtime::v405_isfs+
      nwii::runtime::v405_parent+nwii::runtime::v405_other==
          nwii::runtime::v405_tail_calls&&
      nwii::runtime::v405_nand<=nwii::runtime::v405_tail_calls&&
      nwii::runtime::v405_cache<=nwii::runtime::v405_tail_calls;
  std::cout<<"V405_NAND_SECOND_TRIAL tail_calls="
           <<nwii::runtime::v405_tail_calls
           <<" completed="<<unsigned(v405_completed)<<std::endl;
  check(v405_completed,"V405 original guest post-48 call census incomplete");'''

def patch(source:str)->str:
    anchors=(STATE,RESET,TRACE,STOP,TRIAL,EXIT_CHECK,
             'V404_NAND_EXTENDED_STOP calls=',
             'V404_NAND_EXTENDED_TRIAL calls=',
             'V403_NAND_CALL_PROVENANCE ctr=',
             'V370_NAND_FLAG_W1C n=')
    if (any(source.count(anchor)!=1 for anchor in anchors) or
        MARKER in source or TRIAL_MARKER in source or
        CHECKPOINT in source or EXIT_MARKER in source or
        'v405_tail_calls' in source or
        not (1<=source.count('try{run_game(c);}')<=16)):
        raise ValueError('geometry')
    out=source.replace(STATE,STATE_NEXT,1)
    out=out.replace(RESET,RESET_NEXT,1)
    out=out.replace(TRACE,TRACE_NEXT,1)
    out=out.replace(STOP,STOP_NEXT,1)
    out=out.replace(TRIAL,TRIAL_NEXT,1)
    out=out.replace(EXIT_CHECK,EXIT_OBSERVER,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL_MARKER)!=1 or
        out.count(CHECKPOINT)!=1 or out.count(EXIT_MARKER)!=1 or
        out.count(EXIT_OBSERVER)!=1 or
        out.count(TRACE_NEXT)!=1 or out.count(STOP_NEXT)!=1 or
        out.count('if(owned||v396_calls==96u){')!=1 or
        out.count('V404_NAND_EXTENDED_STOP calls=')!=1 or
        out.count('V403_NAND_CALL_PROVENANCE ctr=')!=1 or
        out.count('try{run_game(c);}')!=source.count('try{run_game(c);}') or
        out.count('V370_NAND_FLAG_W1C n=')!=1):
        raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_96_call_harness',type=Path)
    p.add_argument('next_private_96_call_observer',type=Path)
    args=p.parse_args()
    try:
        if args.next_private_96_call_observer.exists() or args.next_private_96_call_observer.is_symlink():
            raise ValueError('output_exists')
        with args.next_private_96_call_observer.open('x',encoding='utf-8') as f:
            f.write(patch(args.prior_private_96_call_harness.read_text(encoding='utf-8')))
    except (ValueError,OSError) as exc:
        reason=str(exc) if isinstance(exc,ValueError) else 'io'
        if reason not in {'geometry','route','io','output_exists'}:
            reason='other'
        print(f'V405_NAND_SECOND_ERROR reason={reason}',file=sys.stderr)
        print('V405_NAND_SECOND_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V405_NAND_SECOND_ROUTE installed=1 original_guest=1 cap96=1 read_only=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
