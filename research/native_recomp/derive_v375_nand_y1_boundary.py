#!/usr/bin/env python3
"""V375: verify exact preemptible original guest boundary for NAND Y1.

V374 published one real native reply; V373 saw Y1 and guest EE enabled.
This probe distinguishes an eligible IRQ from an actually resumable guest
function-entry boundary, without entering the IRQ or modifying any state.
Only bounded public booleans/classes leave the owner runner.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
PRIOR='V374_NAND_REPLY_GATE n='
MARKER='V375_NAND_Y1_BOUNDARY n='
INJECTION=r"""
  // V375: classify only a real, asserted, interrupt-eligible Y1 reply.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     !ipc70_bus.pending_native_ios_request()&&
     ipc70_bus.external_exception_pending(ctx.msr)){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool y1=ctrl.has_value()&&((*ctrl&M::Y1)!=0u)&&
                  ((*ctrl&M::Y2)==0u);
    const bool pending_flag=flag.has_value()&&
                  ((*flag&H::IPC_PPC)!=0u);
    if(y1&&pending_flag){
      static unsigned v375_count=0u;
      if(v375_count<24u){
        ++v375_count;
        const bool call=(ctx.pc==addr);
        const bool running=ctx.is_running;
        const bool dispatch_free=!ctx.dispatch_saved_ctx;
        const bool aligned=ctx.pc!=0u&&(ctx.pc&3u)==0u;
        const bool mode=(ctx.msr&undercover::wii::ExternalUnsupportedMsr)==0u;
        const bool ee=(ctx.msr&B::MSR_EE)!=0u;
        bool installed=true;
        for(size_t i=0u;i<irq74_vector.size();++i){
          const uint32_t at=undercover::wii::ExternalVector+uint32_t(i);
          if(ctx.mmu.get_ptr(at)==nullptr||ctx.mmu.read8(at)!=irq74_vector[i]){
            installed=false;break;
          }
        }
        const bool preemptible=call&&running&&dispatch_free&&
             aligned&&mode&&installed&&ee;
        // Category 1 is original OSRestoreInterrupts. Category 2 is
        // original IPC/IRQ handling code. Category 3 is any other guest
        // executable function entry, not an unverified address dump.
        const unsigned site=addr==0x805265d4u?1u:
             (addr==0x80519318u||addr==0x80526ce0u)?2u:3u;
        std::cout<<"V375_NAND_Y1_BOUNDARY n="<<v375_count
                 <<" call="<<unsigned(call)
                 <<" running="<<unsigned(running)
                 <<" dispatch="<<unsigned(dispatch_free)
                 <<" aligned="<<unsigned(aligned)
                 <<" mode="<<unsigned(mode)
                 <<" ee="<<unsigned(ee)
                 <<" installed="<<unsigned(installed)
                 <<" preemptible="<<unsigned(preemptible)
                 <<" site="<<site
                 <<" drained="<<unsigned(ipc70_bus.services().queued_replies()==0u)
                 <<std::endl;
      }
    }
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or
        source.count('V373_NAND_IRQ_TIMELINE n=')!=1 or
        'native_external_irq.h' not in source or
        'irq74_vector' not in source or MARKER in source or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2):
        raise ValueError('V375 authentic Y1 call seam changed')
    updated=source.replace(HEAD,HEAD+INJECTION,1)
    if(updated.count(MARKER)!=1 or
       updated.replace(HEAD+INJECTION,HEAD,1)!=source):
        raise ValueError('V375 original guest source transformation not reversible')
    return updated

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('native_harness',type=Path)
    p.add_argument('output_harness',type=Path)
    args=p.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError('output_exists')
        with args.output_harness.open('x',encoding='utf-8') as out:
            out.write(patch(args.native_harness.read_text(encoding='utf-8')))
    except (OSError,ValueError):
        print('V375_NAND_Y1_BOUNDARY installed=0',file=sys.stderr)
        return 1
    print('V375_NAND_Y1_BOUNDARY installed=1 original_guest=1 read_only=1 bounded=24')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
