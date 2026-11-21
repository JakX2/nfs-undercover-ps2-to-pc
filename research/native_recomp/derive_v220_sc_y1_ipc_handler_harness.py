#!/usr/bin/env python3
"""V220 execute real negative Y1 OSDisableScheduler into IPC callback.

V219 verified execution of the third interrupt dispatcher through
OSGetTime and entry to OSDisableScheduler. Execute that original PPC
function and the Wii dispatcher indirect call to the *registered*
IPCInterruptHandler at 0x80519318, retaining actual IOS_Open=-4.
No guest register, branch, memory or response is fabricated.
"""
import argparse
from pathlib import Path
from derive_v219_sc_y1_osdisable_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v178_sc_reply_burst_harness import V98_ACTIVE
STOP='''    ++v219_disable_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v219_disable_seen;
    v220_disable_inst=ctx.inst_count;
    return; // real OSDisableScheduler and original IRQ callback dispatch
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v219_disable_seen==1u&&v220_ipc_seen==0u&&
     addr==0x80519318u&&ctx.pc==addr){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool context=ctx.gpr[3]==4u&&ctx.gpr[4]==THREAD;
    const bool caller=ctx.lr==0x80526cacu;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          ctx.inst_count>v220_disable_inst;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V220_NEG_IPC irq="<<irq<<" reply="<<reply
             <<" context="<<context<<" caller="<<caller
             <<" guest="<<guest<<" masked="<<masked
             <<" sc="<<sc<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq,"V220_NEG_IPC source-owned Y1 signal check failed");
    check(reply,"V220_NEG_IPC source-owned negative response check failed");
    check(context,"V220_NEG_IPC source-owned OS IRQ context check failed");
    check(caller,"V220_NEG_IPC source-owned IRQ caller ABI check failed");
    check(guest,"V220_NEG_IPC source-owned guest SDA and instruction progress check failed");
    check(masked,"V220_NEG_IPC source-owned guest EE state check failed");
    check(sc,"V220_NEG_IPC source-owned SC status check failed");
    check(irq&&reply&&context&&caller&&guest&&masked&&sc,
          "V220 original third Y1 negative reply did not enter registered IPC handler");
    ++v220_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V220_SCOPED_V98='''   if(post97_return==1u&&post98_node&&v219_disable_seen==0u){'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v217_dispatch_seen==1u&&
            nwii::runtime::v218_next_seen==1u&&
            nwii::runtime::v219_disable_seen==1u&&
            nwii::runtime::v220_ipc_seen==1u&&
            !c.is_running&&c.pc==0x80519318u&&c.lr==0x80526cacu&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V220 real negative reply Y1 registered IPC handler checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    # V98's verified NAND-registration assertion assumes the earlier
    # IOS state (no IRQ and no response waiting). The authentic third
    # Y1 interrupt now has IRQ high and a negative reply already on
    # the wire. Retain V98 checks until V219's original scheduler
    # boundary, then silence only that stale phase observer.
    if s.count(V98_ACTIVE)!=1:
        raise ValueError("V220 original NAND observer guard changed")
    s=once(s,V98_ACTIVE,V220_SCOPED_V98)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V220 authenticated V219 scheduler entry changed")
    s=once(s,STATE,STATE+'''
 static unsigned v220_ipc_seen=0u;
 static uint64_t v220_disable_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v220_ipc_seen=0u;
     nwii::runtime::v220_disable_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
