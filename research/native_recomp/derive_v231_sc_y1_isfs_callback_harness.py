#!/usr/bin/env python3
"""V231 original PowerPC indirect ISFS callback entry after third negative Y1.

V230 verified original OSSetCurrentContext entry after authentic IPC
reply handling and Hollywood interrupt W1C. This stage executes that
original context setter and follows the bctrl to the V225 AOT-rooted
_isfsFuncCb. No artificial guest call, IOS status or register mutation.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v230_sc_y1_context_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    ++v230_context_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v230_context_seen;
    v231_context_inst=ctx.inst_count;
    return; // run genuine original OSSetCurrentContext and indirect call
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v230_context_seen==1u&&
     v231_callback_seen==0u&&ctx.pc==addr&&
     addr==0x804f0e04u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&(M::Y1|M::Y2))==0u)&&
          ((*flag&H::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool wire=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const uint32_t request=ctx.gpr[31];
    const bool header=request<=0xffffffe0u&&
          ctx.mmu.get_ptr(request)!=nullptr&&
          ctx.mmu.get_ptr(request+39u)!=nullptr;
    const bool selected=header&&
          ctx.mmu.read32(request+32u)==addr;
    const bool same_request=header&&
          (request&0x1fffffffu)==v183_second_phys;
    const bool callback_abi=ctx.lr==0x805192acu&&
          ctx.gpr[3]==uint32_t(IOS::Invalid);
    const bool userdata=header&&
          ctx.gpr[4]==ctx.mmu.read32(request+36u);
    const bool guest=ctx.inst_count>v231_context_inst&&
          ctx.gpr[13]==v147_first_r13&&
          (ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V231_ISFS_CALLBACK clear="<<clear
             <<" wire="<<wire<<" header="<<header
             <<" selected="<<selected<<" same="<<same_request
             <<" abi="<<callback_abi<<" userdata="<<userdata
             <<" guest="<<guest<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(clear&&wire&&header&&selected&&same_request&&
          callback_abi&&userdata&&guest&&sc,
          "V231 original third negative IOS reply indirect ISFS callback ABI differs");
    v231_target_pc=addr;v231_target_lr=ctx.lr;
    ++v231_callback_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=nwii::runtime::ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      check(stopped&&nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v227_ack_seen==1u&&
            nwii::runtime::v228_next_seen==1u&&
            nwii::runtime::v229_call_seen==1u&&
            nwii::runtime::v230_context_seen==1u&&
            nwii::runtime::v231_callback_seen==1u&&
            ctrl.has_value()&&flag.has_value()&&
            ((*ctrl&(M::Y1|M::Y2))==0u)&&
            ((*flag&H::IPC_PPC)==0u)&&
            !nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid&&
            !c.is_running&&c.pc==0x804f0e04u&&c.lr==0x805192acu&&
            c.gpr[3]==uint32_t(undercover::wii::StmIos::Invalid)&&
            c.mmu.read8(c.gpr[13]-3176u)==1u,
            "V231 original negative IOS_Open reached ISFS callback with authentic ABI");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V231 inherited original V230 OSSetCurrentContext changed")
    s=once(s,STATE,STATE+'''
 static unsigned v231_callback_seen=0u;
 static uint64_t v231_context_inst=0u;
 static uint32_t v231_target_pc=0u,v231_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v231_callback_seen=0u;
     nwii::runtime::v231_context_inst=0u;
     nwii::runtime::v231_target_pc=nwii::runtime::v231_target_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
