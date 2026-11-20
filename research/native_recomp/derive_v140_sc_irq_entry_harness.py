#!/usr/bin/env python3
"""V140 enter the genuine installed Wii external vector after V139 SC IOS ACK.

The host helper models PPC external-interrupt *entry* at an already-instrumented
guest function-entry dispatch boundary. The owner-original vector/handler is not
executed in this test. Never write synthetic success state or complete the IOS
reply. All data from owner-generated translation remain private.
"""
import argparse
from pathlib import Path
from derive_v139_sc_ios_service_harness import derive as previous

STOP= '''     ++post136_seen;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }'''

NEW= '''     ++post136_seen;
     const uint32_t v140_resume=ctx.pc;
     const uint32_t v140_msr=ctx.msr;
     const uint32_t v140_lr=ctx.lr,v140_ctr=ctx.ctr,v140_xer=ctx.xer;
     const auto v140_gprs=ctx.gpr;
     const bool v140_pending=ipc70_bus.external_exception_pending(ctx.msr);
     const auto v140_entry=undercover::wii::enter_external_irq(
           ctx,ipc70_bus,irq74_vector,true);
     const bool v140_vector=v140_entry==undercover::wii::ExternalEntry::Entered&&
           ctx.pc==undercover::wii::ExternalVector;
     const bool v140_saved=ctx.srr0==v140_resume&&
           ctx.srr1==(v140_msr&undercover::wii::ExternalSrr1Mask)&&
           ctx.msr==(v140_msr&~undercover::wii::ExternalMsrClear);
     const bool v140_regs=ctx.gpr==v140_gprs&&ctx.lr==v140_lr&&
           ctx.ctr==v140_ctr&&ctx.xer==v140_xer;
     std::cout<<"V140_SC_IRQ_ENTRY pending="<<v140_pending
              <<" vector="<<v140_vector<<" saved="<<v140_saved
              <<" regs="<<v140_regs<<" queued="<<
              (ipc70_bus.services().queued_replies()==1u)<<std::endl;
     check(v140_pending&&v140_vector&&v140_saved&&v140_regs&&
           ipc70_bus.services().queued_replies()==1u,
           "V140 SC IOS ACK failed to enter installed original external vector");
     // Record the original callable stop, not the newly selected vector.
     // The actual guest PPC handler must be executed in a later test.
     post90_target=addr;observed_stop_pc=v140_resume;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }'''

def derive(source: str) -> str:
    s=previous(source)
    if s.count(STOP)!=1:
        raise ValueError("V140 original SC third-entry test stop changed")
    return s.replace(STOP,NEW,1)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    a=parser.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
