#!/usr/bin/env python3
"""V217 execute original third Y1 exception handler to IRQ dispatcher.

V216 owner-original reached the real Wii exception handler 0x80526CE0
through native original PowerPC vector instructions. Continue this handler
to the genuine 0x80526A3C IRQ dispatcher while retaining the second
IOS_Open's actual negative -4 reply and the original game CPU state.
"""
import argparse
from pathlib import Path
from derive_v216_sc_y1_handler_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''      ++v216_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }'''
CONTINUE='''      v217_handler_inst=ctx.inst_count;
      ++v216_handler_seen;
      return; // original Wii exception-handler PowerPC code runs
    }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v216_handler_seen==1u&&v217_dispatch_seen==0u&&
     addr==0x80526a3cu&&ctx.pc==addr){
    using VB=undercover::wii::IosBus;
    using VM=undercover::wii::IpcMailbox;
    using VH=undercover::wii::HollywoodIrq;
    using VI=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(VB::IPC+VM::PPCCTRL);
    const auto flag=ipc70_bus.read32(VB::IPC+VH::PPC_FLAG);
    const bool index=ctx.gpr[3]==4u;
    const bool context=ctx.gpr[4]==THREAD;
    const bool masked=(ctx.msr&VB::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&VM::Y1)!=0u)&&((*ctrl&VM::Y2)==0u)&&
          ((*flag&VH::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==VI::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==VI::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==VI::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          ctx.inst_count>v217_handler_inst;
    const bool saved=ctx.mmu.read32(THREAD+408u)==v215_saved_pc;
    std::cout<<"V217_NEG_DISPATCH index="<<index<<" context="<<context
             <<" masked="<<masked<<" irq="<<irq<<" reply="<<reply
             <<" guest="<<guest<<" saved="<<saved
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(index&&context&&masked&&irq&&reply&&guest,
          "V217 original third Y1 handler did not dispatch actual negative IOS reply");
    ++v217_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v217_dispatch_seen==1u&&
            !c.is_running&&c.pc==0x80526a3cu&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V217 original negative IOS Y1 handler did not reach IRQ dispatcher");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V217 authenticated V216 handler stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v217_dispatch_seen=0u;
 static uint64_t v217_handler_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v217_dispatch_seen=0u;
     nwii::runtime::v217_handler_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
