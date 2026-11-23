#!/usr/bin/env python3
"""V374: native queued IOS reply at the original NAND scheduling boundary.

At an authentic OSRestoreInterrupts entry, advance exactly one already
validated native IOS response only after the original Broadway code has
cleared Y2 and Hollywood PPC_FLAG. No fabricated status, guest context
mutation, synthetic handler, or automatic pumping on MMIO writes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
INCLUDE='#include "wii_ios_yield_scheduler.h"'
NEW_INCLUDE='#include "wii_nand_ios_reply_yield.h"\n'
PRIOR='V373_NAND_IRQ_TIMELINE n='
OTHER='V361_NAND_IOS_YIELD n='
MARKER='V374_NAND_REPLY_GATE n='

INJECTION=r"""
  // V374: only the authenticated original NAND OSRestoreInterrupts entry.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     addr==0x805265d4u&&!ipc70_bus.pending_native_ios_request()&&
     ipc70_bus.services().queued_replies()>0u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto prev_ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto prev_flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool yclear=prev_ctrl.has_value()&&
                      ((*prev_ctrl&(M::Y1|M::Y2))==0u);
    const bool flagclear=prev_flag.has_value()&&
                         ((*prev_flag&H::IPC_PPC)==0u);
    const bool irq_before=ipc70_bus.external_irq_level();
    const auto result=undercover::wii::service_deferred_reply_at_guest_boundary(
                         ipc70_bus,ctx.msr);
    const auto post_ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const bool y1=post_ctrl.has_value()&&((*post_ctrl&M::Y1)!=0u);
    static unsigned v374_count=0u;
    if(v374_count<16u){
      ++v374_count;
      std::cout<<"V374_NAND_REPLY_GATE n="<<v374_count
               <<" yclear="<<unsigned(yclear)
               <<" flagclear="<<unsigned(flagclear)
               <<" irq_before="<<unsigned(irq_before)
               <<" fired="<<unsigned(result.has_value())
               <<" pump="<<unsigned(result.has_value()?result->progress:
                                       undercover::wii::StmIos::Pump::Idle)
               <<" y1="<<unsigned(y1)
               <<" queued="<<unsigned(ipc70_bus.services().queued_replies()>0u)
               <<" irq_after="<<unsigned(ipc70_bus.external_irq_level())
               <<" eligible="<<unsigned(ipc70_bus.external_exception_pending(ctx.msr))
               <<std::endl;
    }
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(INCLUDE)!=1 or
        source.count(PRIOR)!=1 or source.count(OTHER)!=1 or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        MARKER in source or NEW_INCLUDE.strip() in source):
        raise ValueError('V374 original native scheduling seam changed')
    output=source.replace(INCLUDE,INCLUDE+'\n'+NEW_INCLUDE,1)
    output=output.replace(HEAD,HEAD+INJECTION,1)
    if (output.count(MARKER)!=1 or output.count(NEW_INCLUDE.strip())!=1 or
        output.replace(HEAD+INJECTION,HEAD,1).replace(
            INCLUDE+'\n'+NEW_INCLUDE,INCLUDE,1)!=source):
        raise ValueError('V374 source transformation not reversible')
    return output

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_harness',type=Path)
    parser.add_argument('output_harness',type=Path)
    args=parser.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError('output_exists')
        with args.output_harness.open('x',encoding='utf-8') as output:
            output.write(patch(args.source_harness.read_text(encoding='utf-8')))
    except (OSError,ValueError):
        print('V374_NAND_REPLY_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V374_NAND_REPLY_ROUTE installed=1 original_guest=1 authentic_yield=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
