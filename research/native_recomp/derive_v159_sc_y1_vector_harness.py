#!/usr/bin/env python3
"""V159 admit pending SC SYSCONF Y1 through the existing PPC exception bridge.

Only after V158's original OSLoadContext/RFI restores the *game-selected*
running context and MSR EE=1, allow the already-pending, native IOS reply's Y1
interrupt to enter the authentic installed 0x80000500 Broadway vector.
This is the tested host hardware exception bridge, NOT synthesized game code,
forced guest registers, an extra IOS tick, or an original callback execution.
The vector body itself is not executed until a subsequent checkpoint.
"""
import argparse
from pathlib import Path
from derive_v158_sc_rfi_restore_harness import (
    derive as previous, STATE, RESET, RFI_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL,
)
from derive_v154_sc_scheduler_next_harness import V154_CHECK

STOP='''    ++v158_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v158_rfi_seen;
    const auto original_pc=ctx.pc;
    const auto original_msr=ctx.msr;
    const auto original_gprs=ctx.gpr;
    const auto original_lr=ctx.lr,original_ctr=ctx.ctr,original_xer=ctx.xer;
    const bool pending=ipc70_bus.external_exception_pending(ctx.msr);
    const bool safe=!ctx.dispatch_saved_ctx;
    check(pending&&safe&&v158_selected_thread,
          "V159 SC reply Y1 was not eligible at authentic restored guest boundary");
    const auto result=undercover::wii::enter_external_irq(
          ctx,ipc70_bus,irq74_vector,true);
    const bool entered=result==undercover::wii::ExternalEntry::Entered;
    const bool vector=ctx.pc==undercover::wii::ExternalVector&&
          ctx.srr0==original_pc&&
          ctx.srr1==(original_msr&undercover::wii::ExternalSrr1Mask)&&
          ctx.msr==(original_msr&~undercover::wii::ExternalMsrClear);
    const bool regs=ctx.gpr==original_gprs&&
          ctx.lr==original_lr&&ctx.ctr==original_ctr&&ctx.xer==original_xer;
    const bool masked=!ipc70_bus.external_exception_pending(ctx.msr)&&
          ipc70_bus.external_irq_level();
    std::cout<<"V159_SC_Y1_VECTOR pending="<<pending<<" safe="<<safe
             <<" entered="<<entered<<" vector="<<vector
             <<" regs="<<regs<<" masked="<<masked<<std::endl;
    check(entered&&vector&&regs&&masked,
          "V159 native PPC external exception entry corrupted original SC Y1 state");
    ++v159_vector_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
VECTOR_GATE='''             nwii::runtime::v154_next_seen==1u&&
             ((c.pc>=0x80400000u&&c.pc<0x80600000u&&!c.is_running)||
              (nwii::runtime::v159_vector_seen==1u&&
               c.pc==undercover::wii::ExternalVector&&
               c.srr0==nwii::runtime::v158_expected_pc&&
               c.srr1==(nwii::runtime::v158_expected_msr&
                         undercover::wii::ExternalSrr1Mask)&&
               !c.is_running));'''
NEXT_TRIAL='''       check(nwii::runtime::v159_vector_seen==1u&&
             nwii::runtime::v158_rfi_seen==1u&&
             c.pc==undercover::wii::ExternalVector&&
             c.srr0==nwii::runtime::v158_expected_pc&&
             c.srr1==(nwii::runtime::v158_expected_msr&
                       undercover::wii::ExternalSrr1Mask)&&
             !c.is_running,
             "V159 SC reply Y1 did not enter authentic native PPC external vector");'''

def once(source: str, old: str, new: str)->str:
    n=source.count(old)
    if n!=1:
        raise ValueError(f"V159 source-only anchor count={n}: {old[:70]}")
    return source.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if RFI_OBSERVER.count(STOP)!=1:
        raise ValueError("V159 original RFI checkpoint stop no longer matches")
    s=once(s,STATE,STATE+"\n static unsigned v159_vector_seen=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v159_vector_seen=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,V154_CHECK,VECTOR_GATE)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
