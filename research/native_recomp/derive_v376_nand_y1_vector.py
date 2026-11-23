#!/usr/bin/env python3
"""V376: enter the verified original Wii external vector on actual NAND Y1.

V374 proved native IOS reply publication; V373 then proved eligibility at an
original guest call boundary. Interrupt only at an aligned, not-yet-executed
guest function entry with MSR.EE enabled, an installed original vector, and
the actual Broadway Y1/Hollywood interrupt hardware. Stop immediately after
PowerPC hardware exception entry. Handler execution is a later milestone.
No fake guest branches, no IOS ticks, no synthesized callback or return code.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from derive_v375_nand_y1_boundary import INJECTION as BOUNDARY_INJECTION

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
INCLUDE='#include "native_external_irq.h"'
ADD_INCLUDE='#include "wii_nand_y1_exception.h"'
PRIOR="V374_NAND_REPLY_GATE n="
TIMELINE="V373_NAND_IRQ_TIMELINE n="
MARKER="V376_NAND_VECTOR n="
INJECTION=r"""
  // V376: only the verified original NAND Y1 at an interruptible call.
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
    const bool flagged=flag.has_value()&&((*flag&H::IPC_PPC)!=0u);
    static unsigned v375_seen=0u;
    if(y1&&flagged&&v375_seen<16u){
      ++v375_seen;
      const bool safe=ctx.is_running&&ctx.pc==addr&&ctx.pc!=0u&&
                      !(ctx.pc&3u)&&!ctx.dispatch_saved_ctx&&
                      !(ctx.msr&undercover::wii::ExternalUnsupportedMsr);
      bool installed=true;
      for(size_t i=0u;i<irq74_vector.size();++i){
        const uint32_t at=undercover::wii::ExternalVector+uint32_t(i);
        if(ctx.mmu.get_ptr(at)==nullptr||
           ctx.mmu.read8(at)!=irq74_vector[i]){
          installed=false;break;
        }
      }
      const uint32_t resume=ctx.pc,msr=ctx.msr;
      const uint32_t lr=ctx.lr,ctr=ctx.ctr,xer=ctx.xer;
      const uint64_t instructions=ctx.inst_count;
      const auto gprs=ctx.gpr;
      const auto result=safe&&installed?
          undercover::wii::enter_queued_nand_y1(
              ctx,ipc70_bus,irq74_vector,true):
          undercover::wii::ExternalEntry::Deferred;
      const bool entered=result==undercover::wii::ExternalEntry::Entered&&
                         ctx.pc==undercover::wii::ExternalVector;
      const bool saved=entered&&ctx.srr0==resume&&
                       ctx.srr1==(msr&undercover::wii::ExternalSrr1Mask)&&
                       ctx.msr==(msr&~undercover::wii::ExternalMsrClear);
      const bool regs=ctx.gpr==gprs&&ctx.lr==lr&&ctx.ctr==ctr&&
                      ctx.xer==xer&&ctx.inst_count==instructions;
      const bool irq=ipc70_bus.external_irq_level()&&
                     !ipc70_bus.external_exception_pending(ctx.msr);
      std::cout<<"V376_NAND_VECTOR n="<<v375_seen
               <<" y1="<<unsigned(y1)
               <<" safe="<<unsigned(safe)
               <<" installed="<<unsigned(installed)
               <<" entered="<<unsigned(entered)
               <<" saved="<<unsigned(saved)
               <<" regs="<<unsigned(regs)
               <<" irq_masked="<<unsigned(irq)
               <<" queued="<<unsigned(ipc70_bus.services().queued_replies()>0u)
               <<std::endl;
      if(entered){
        check(saved&&regs&&irq&&y1&&safe&&installed,
              "V376 authentic NAND Y1 hardware exception entry changed guest state");
        // The vector is selected, not yet executed. Never return to the
        // original preempted function body with its PC now at 0x80000500.
        ctx.is_running=false;throw ExceptionStop{};
      }
    }
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(HEAD+BOUNDARY_INJECTION)!=1 or
        source.count(PRIOR)!=1 or
        source.count(TIMELINE)!=1 or source.count('V375_NAND_Y1_BOUNDARY n=')!=1 or
        source.count(INCLUDE)!=1 or ADD_INCLUDE in source or
        'irq74_vector' not in source or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or MARKER in source):
        raise ValueError("V376 authenticated guest IRQ entry seam changed")
    output=source.replace(INCLUDE,INCLUDE+'\n'+ADD_INCLUDE,1)
    output=output.replace(HEAD+BOUNDARY_INJECTION,HEAD+BOUNDARY_INJECTION+INJECTION,1)
    if output.count(MARKER)!=1 or output.replace(HEAD+BOUNDARY_INJECTION+INJECTION,HEAD+BOUNDARY_INJECTION,1).replace(INCLUDE+'\n'+ADD_INCLUDE,INCLUDE,1)!=source:
        raise ValueError("V376 source-only interrupt injection not reversible")
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("output_exists")
        with args.output.open("x",encoding="utf-8") as out:
            out.write(patch(args.source.read_text(encoding="utf-8")))
    except (ValueError,OSError):
        print("V376_NAND_VECTOR_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V376_NAND_VECTOR_ROUTE installed=1 original_guest=1 bounded=16 stop_at_vector=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
