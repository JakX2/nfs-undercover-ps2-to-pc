#!/usr/bin/env python3
"""V161 execute original SC Y1 exception-handler body into IRQ dispatcher.

After V160 verified original vector -> handler 0x80526CE0, execute that
original guest handler until its expected dispatch call 0x80526A3C.
The prior STM (V75/V76) handler observer is phase-specific; this additional
read-only probe runs before it, without changing PPC code, guest memory,
IOS reply state, exception registers or IRQ acknowledgements.
"""
import argparse
from pathlib import Path
from derive_v160_sc_y1_vector_handler_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    NEXT_TRIAL as PREVIOUS_TRIAL, V160_PC
)

STOP='''      ++v160_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }'''
CONTINUE='''      v161_handler_inst=ctx.inst_count;
      ++v160_handler_seen;
      return; // run original Broadway external interrupt-handler body
    }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v160_handler_seen==1u&&v161_dispatch_seen==0u&&addr==0x80526a3cu){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool index=ctx.gpr[3]==4u;
    const bool context=ctx.gpr[4]==THREAD;
    const bool saved_pc=ctx.mmu.read32(THREAD+408u)==v158_expected_pc;
    const bool saved_msr=ctx.mmu.read32(THREAD+412u)==v158_expected_msr;
    const bool running=ctx.mmu.read16(THREAD+712u)==2u;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool advanced=ctx.pc==addr&&ctx.inst_count>v161_handler_inst;
    std::cout<<"V161_SC_Y1_DISPATCH index="<<index<<" context="<<context
             <<" saved_pc="<<saved_pc<<" saved_msr="<<saved_msr
             <<" running="<<running<<" masked="<<masked
             <<" irq="<<irq<<" advanced="<<advanced
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(index&&context&&masked&&irq&&advanced,
          "V161 original SC second reply IRQ handler did not reach dispatcher");
    ++v161_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V161_PC='''             (c.pc==undercover::wii::ExternalVector||
              (nwii::runtime::v160_handler_seen==1u&&
               c.pc==0x80526ce0u)||
              (nwii::runtime::v161_dispatch_seen==1u&&
               c.pc==0x80526a3cu))&&'''
V160_FINAL_PC='''             c.pc==0x80526ce0u&&!c.is_running,'''
V161_FINAL_PC='''             (c.pc==0x80526ce0u||
              (nwii::runtime::v161_dispatch_seen==1u&&
               c.pc==0x80526a3cu))&&!c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v161_dispatch_seen==1u&&
             nwii::runtime::v160_handler_seen==1u&&
             nwii::runtime::v160_vector_seen==1u&&
             nwii::runtime::v159_vector_seen==1u&&
             c.pc==0x80526a3cu&&!c.is_running,
             "V161 original SC reply exception handler did not dispatch guest IRQ");'''

def once(s: str, old: str, new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V161 original-free source anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_TRIAL.count(V160_FINAL_PC)!=1 or s.count(STOP)!=1:
        raise ValueError("V161 inherited SC handler stop or trial differs")
    s=once(s,STATE,STATE+'''
 static unsigned v161_dispatch_seen=0;
 static uint64_t v161_handler_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v161_dispatch_seen=0u;
     nwii::runtime::v161_handler_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,V160_PC,V161_PC)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V160_FINAL_PC,V161_FINAL_PC,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
