#!/usr/bin/env python3
"""V216 genuine PowerPC execution of third Wii exception vector.

After V215 delivered the original second IOS_Open negative result over Y1
and entered 0x80000500, run the installed original Wii external vector
instructions until original handler 0x80526CE0. Verify actual -4 wire
response, frame/MSR ABI, interrupt and context without replacing guest code.
"""
import argparse
from pathlib import Path
from derive_v215_sc_y1_negative_vector_harness import (
    derive as previous, CONTINUE as PREVIOUS_CONTINUE,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    ++v215_vector_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CONTINUE='''    ++v215_vector_seen;
    v216_start_inst=ctx.inst_count;
    return true; // original Wii installed external vector begins executing
  }
'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v216_handler_seen==0u){
    using VB=undercover::wii::IosBus;
    using VM=undercover::wii::IpcMailbox;
    using VH=undercover::wii::HollywoodIrq;
    using VI=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(VB::IPC+VM::PPCCTRL);
    const auto flag=ipc70_bus.read32(VB::IPC+VH::PPC_FLAG);
    const bool pending_y1=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&VM::Y1)!=0u)&&((*ctrl&VM::Y2)==0u)&&
          ((*flag&VH::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==VI::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==VI::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==VI::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    if(addr==undercover::wii::ExternalVector){
      const bool saved=ctx.srr0==v215_saved_pc&&
            ctx.srr1==(v215_saved_msr&undercover::wii::ExternalSrr1Mask);
      const bool regs=ctx.gpr==v215_original_gprs&&
            ctx.lr==v215_saved_lr&&ctx.ctr==v215_saved_ctr&&
            ctx.xer==v215_saved_xer;
      bool bytes=true;
      for(size_t i=0;i<irq74_vector.size();++i)
        bytes&=ctx.mmu.read8(undercover::wii::ExternalVector+uint32_t(i))==
               irq74_vector[i];
      const bool masked=(ctx.msr&VB::MSR_EE)==0u&&
            !ipc70_bus.external_exception_pending(ctx.msr);
      std::cout<<"V216_Y1_ENTRY saved="<<saved<<" regs="<<regs
               <<" bytes="<<bytes<<" masked="<<masked
               <<" y1="<<pending_y1<<" negative="<<reply<<std::endl;
      check(saved&&regs&&bytes&&masked&&pending_y1&&reply,
            "V216 second negative Y1 original installed Wii vector state invalid");
      ++v216_vector_seen;
      return; // execute original Wii vector instructions unmodified
    }
    if(addr==0x80526ce0u){
      const bool index=ctx.gpr[3]==4u;
      const bool context=ctx.gpr[4]==THREAD||ctx.gpr[4]==IDLE_CONTEXT;
      const bool vector=v216_vector_seen==1u&&ctx.pc==addr;
      const bool masked=(ctx.msr&VB::MSR_EE)==0u&&
            !ipc70_bus.external_exception_pending(ctx.msr);
      const bool progressed=ctx.inst_count>v216_start_inst;
      std::cout<<"V216_Y1_HANDLER vector="<<vector
               <<" irq="<<pending_y1<<" reply="<<reply
               <<" index="<<index<<" context="<<context
               <<" masked="<<masked<<" progressed="<<progressed
               <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
               <<std::dec<<std::endl;
      check(vector&&pending_y1&&reply&&index&&context&&masked&&progressed,
            "V216 original second negative IOS Y1 vector did not reach guest handler");
      ++v216_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }
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
            !c.is_running&&c.pc==0x80526ce0u&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V216 original negative Y1 vector instructions did not reach handler");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_CONTINUE.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V216 authenticated V215 original Y1 vector boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v216_vector_seen=0u,v216_handler_seen=0u;
 static uint64_t v216_start_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v216_vector_seen=nwii::runtime::v216_handler_seen=0u;
     nwii::runtime::v216_start_inst=0u;''')
    s=once(s,PREVIOUS_CONTINUE,PREVIOUS_CONTINUE.replace(STOP,CONTINUE,1))
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
