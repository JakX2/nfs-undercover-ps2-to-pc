#!/usr/bin/env python3
"""V208: publish second original IOS_Open reply at owner-verified Wii guest yield.

The V207 owner trace reached PC 0x80529434 / LR 0x80526CB0 after the
authentic second-Y2 PPCCTRL and Hollywood W1C, with a single completion
queued and SC state unchanged. Permit exactly ONE deterministic native
IOS scheduler step at this already-proven PowerPC yield point. Observe
the real original request-buffer reply, Y1 IRQ and unchanged guest CPU.
Do not synthesize any MMIO, patch PowerPC registers, or force SC ready.
"""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v207_next_pc=addr;v207_next_lr=ctx.lr;
    v207_sc=sc;v207_queue=queued;v207_reply=replied;
    ++v207_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
PUBLISH='''    check(addr==0x80529434u&&ctx.lr==0x80526cb0u&&
          ack&&irq_down&&queued&&open&&!replied&&
          guest&&caller&&coherent&&irqflag&&mapped&&sc==1u&&!ee,
          "V208 verified original second Y2 IOS yield boundary differs");
    using S=undercover::wii::StmIos;
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const uint32_t req=v183_second_phys;
    check(req!=0u&&ipc70_ram.valid(req,64u)&&
          ipc70_ram.read32(req)==S::Open&&
          ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request(),
          "V208 second IOS_Open no longer waiting at genuine guest yield");
    const uint32_t pc_before=ctx.pc,lr_before=ctx.lr,msr_before=ctx.msr;
    const uint64_t inst_before=ctx.inst_count;
    std::array<uint32_t,32> gprs_before{};
    for(unsigned i=0u;i<32u;++i)gprs_before[i]=ctx.gpr[i];
    undercover::wii::IosYieldScheduler scheduler(ipc70_bus);
    const auto service=scheduler.service_one(ctx.msr);
    const auto ctrl_after=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag_after=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const auto arm=ipc70_bus.read32(B::IPC+M::ARMMSG);
    const bool step=service.progress==S::Pump::Replied&&
          service.serviced_steps==1u;
    const bool wire=arm.has_value()&&*arm==req&&
          ipc70_ram.read32(req)==S::Reply&&
          ipc70_ram.read32(req+8u)==S::Open;
    const uint32_t fd=ipc70_ram.read32(req+4u);
    const bool opened=fd<S::DescriptorCount&&
          ipc70_bus.services().is_open(fd,S::Device::File);
    const bool signal=ctrl_after.has_value()&&flag_after.has_value()&&
          ((*ctrl_after&M::Y1)!=0u)&&((*ctrl_after&M::Y2)==0u)&&
          ((*flag_after&H::IPC_PPC)!=0u)&&
          ipc70_bus.external_irq_level()&&
          service.broadway_irq_level&&!service.guest_exception_ready;
    const bool drained=ipc70_bus.services().queued_replies()==0u&&
          !ipc70_bus.pending_native_ios_request();
    bool cpu=ctx.pc==pc_before&&ctx.lr==lr_before&&
          ctx.msr==msr_before&&ctx.inst_count==inst_before;
    for(unsigned i=0u;i<32u;++i)cpu&=ctx.gpr[i]==gprs_before[i];
    const bool sc_before=ctx.mmu.read8(ctx.gpr[13]-3176u)==1u;
    std::cout<<"V208_Y2_REPLY step="<<step<<" wire="<<wire
             <<" opened="<<opened<<" signal="<<signal
             <<" drained="<<drained<<" cpu="<<cpu
             <<" sc="<<sc_before<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    // Each condition has a distinct source-only assertion label. Owner
    // diagnostics report only the failing category, never guest data.
    check(step,"V208 second IOS native reply service step failed");
    check(wire,"V208 second IOS original request reply wire failed");
    check(signal,"V208 second IOS Y1 and Hollywood IRQ publication failed");
    check(drained,"V208 second IOS reply queue did not drain");
    check(cpu,"V208 second IOS service unexpectedly modified guest CPU");
    check(sc_before,"V208 second IOS service unexpectedly changed SC status");
    check(opened,"V208 second IOS opened file descriptor kind differs");
    v207_next_pc=addr;v207_next_lr=ctx.lr;
    v207_sc=sc;v207_queue=queued;v207_reply=replied;
    ++v207_next_seen;
    v208_fd=fd;
    ++v208_reply_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
NEXT_END='''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      using S=undercover::wii::StmIos;
      const uint32_t req=nwii::runtime::v183_second_phys;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=nwii::runtime::ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      const auto arm=nwii::runtime::ipc70_bus.read32(B::IPC+M::ARMMSG);
      const bool done=ctrl.has_value()&&flag.has_value()&&arm.has_value()&&
            ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
            ((*flag&H::IPC_PPC)!=0u)&&*arm==req&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.valid(req,64u)&&
            nwii::runtime::ipc70_ram.read32(req)==S::Reply&&
            nwii::runtime::ipc70_ram.read32(req+8u)==S::Open&&
            nwii::runtime::ipc70_ram.read32(req+4u)==nwii::runtime::v208_fd;
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            nwii::runtime::v208_reply_seen==1u&&
            done&&!c.is_running&&c.pc==0x80529434u&&
            c.lr==0x80526cb0u&&
            c.mmu.read8(c.gpr[13]-3176u)==1u,
            "V208 original second IOS reply native publication checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V208 authenticated original second Y2 yield changed")
    s=once(s,STATE,STATE+'''
 static unsigned v208_reply_seen=0u;
 static uint32_t v208_fd=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v208_reply_seen=0u;
     nwii::runtime::v208_fd=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,PUBLISH,1))
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
