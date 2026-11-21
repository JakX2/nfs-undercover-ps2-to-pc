#!/usr/bin/env python3
"""V186 real IOS intake of the second Wii SYSCONF-related Open request.

V185 owner-original confirmed PC 0x80529434/LR 0x80526CB0, command IOS_Open,
visible X1/Y1/Y2 clear, and no reply. This repeats the V153 verified
guest-yield boundary. Perform exactly one native IOS scheduler step and
require a real Starlet Y2 ACK and queued completion. Do not publish a
reply, alter guest PowerPC state, or fake SC readiness. This file is
independently written source only; owner game code remains private.
"""
import argparse
from pathlib import Path
from derive_v185_sc_reply_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
# The original V153 first IOS reply guard is phase-specific. V186 is the
# separately verified second Open ACK, when Y2 is set and queued replies=1.
V153_FIRST_REPLY_GUARD='''       check(v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq&&
             nwii::runtime::v149_ack_seen==1u&&
             nwii::runtime::v150_flag_seen==1u&&
             nwii::runtime::v151_next_seen==1u,
             "V153 original SC IRQ did not deliver queued SYSCONF file-open reply");'''
V186_SCOPED_V153_GUARD='''       // The V153 predicate proves the first IOS reply. After the
       // separately authenticated V186 second-request ACK, the original
       // Y1/empty-queue condition cannot still hold: Y2 is asserted and
       // a fresh native completion is queued. Do not change the first
       // phase proof, only accept the strictly verified later checkpoint.
       check((nwii::runtime::v186_ack_seen==1u&&
              nwii::runtime::v185_next_seen==1u&&
              nwii::runtime::v183_second_ctrl==1u&&
              c.pc==0x80529434u&&c.lr==0x80526cb0u&&!c.is_running)||
             (v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq&&
              nwii::runtime::v149_ack_seen==1u&&
              nwii::runtime::v150_flag_seen==1u&&
              nwii::runtime::v151_next_seen==1u),
             "V153 original SC IRQ did not deliver queued SYSCONF file-open reply");'''

STOP='''    v185_target_pc=addr;v185_target_lr=ctx.lr;
    ++v185_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
HANDOFF='''    using V186Bus=undercover::wii::IosBus;
    using V186Mail=undercover::wii::IpcMailbox;
    using V186Irq=undercover::wii::HollywoodIrq;
    using V186Ios=undercover::wii::StmIos;
    const bool v186_route=addr==0x80529434u&&ctx.lr==0x80526cb0u;
    const bool v186_prior=v184_burst_seen==1u&&v184_calls==6u&&
          v183_second_msg==1u&&v183_second_ctrl==1u&&
          v183_second_cmd==V186Ios::Open;
    const auto v186_ctrl=ipc70_bus.read32(V186Bus::IPC+V186Mail::PPCCTRL);
    const auto v186_flags=ipc70_bus.read32(V186Bus::IPC+V186Irq::PPC_FLAG);
    const bool v186_clear=v186_ctrl.has_value()&&v186_flags.has_value()&&
          ((*v186_ctrl&(V186Mail::X1|V186Mail::Y1|V186Mail::Y2))==0u)&&
          ((*v186_flags&V186Irq::IPC_PPC)==0u)&&
          !ipc70_bus.external_irq_level();
    const bool v186_latched=ipc70_bus.pending_native_ios_request();
    const bool v186_open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==V186Ios::Open;
    const bool v186_empty=ipc70_bus.services().queued_replies()==0u;
    const bool v186_sc=status==1u&&mapped&&!changed;
    std::cout<<"V186_IOS_PRE route="<<v186_route<<" prior="<<v186_prior
             <<" intake="<<v186_latched<<" clear="<<v186_clear
             <<" open="<<v186_open<<" idle="<<v186_empty
             <<" sc="<<v186_sc<<std::endl;
    check(v186_route&&v186_prior&&v186_latched&&v186_clear&&v186_open&&
          v186_empty&&v186_sc&&guest&&caller&&coherent,
          "V186 authentic second IOS_Open yield not pending or MMIO unclear");
    const auto v186_pc=ctx.pc,v186_lr=ctx.lr,v186_msr=ctx.msr;
    const auto v186_inst=ctx.inst_count;
    std::array<uint32_t,32> v186_regs{};
    for(unsigned n=0u;n<32u;++n)v186_regs[n]=ctx.gpr[n];
    undercover::wii::IosYieldScheduler scheduler(ipc70_bus);
    const auto v186_result=scheduler.service_one(ctx.msr);
    const auto v186_ctrl_after=ipc70_bus.read32(V186Bus::IPC+V186Mail::PPCCTRL);
    const auto v186_flags_after=ipc70_bus.read32(V186Bus::IPC+V186Irq::PPC_FLAG);
    const bool v186_ack=v186_result.progress==V186Ios::Pump::Ack&&
          v186_result.serviced_steps==1u;
    const bool v186_y2=v186_ctrl_after.has_value()&&
          ((*v186_ctrl_after&V186Mail::Y2)!=0u)&&
          ((*v186_ctrl_after&(V186Mail::X1|V186Mail::Y1))==0u);
    const bool v186_irq=v186_flags_after.has_value()&&
          ((*v186_flags_after&V186Irq::IPC_PPC)!=0u)&&
          ipc70_bus.external_irq_level()&&
          v186_result.broadway_irq_level&&
          v186_result.guest_exception_ready==
             ipc70_bus.external_exception_pending(ctx.msr);
    const bool v186_queued=ipc70_bus.services().queued_replies()==1u;
    const bool v186_consumed=!ipc70_bus.pending_native_ios_request();
    const bool v186_request=ipc70_ram.read32(v183_second_phys)==V186Ios::Open;
    bool v186_cpu=ctx.pc==v186_pc&&ctx.lr==v186_lr&&
          ctx.msr==v186_msr&&ctx.inst_count==v186_inst;
    for(unsigned n=0u;n<32u;++n)v186_cpu&=ctx.gpr[n]==v186_regs[n];
    std::cout<<"V186_SECOND_ACK ack="<<v186_ack<<" y2="<<v186_y2
             <<" irq="<<v186_irq<<" queued="<<v186_queued
             <<" consumed="<<v186_consumed<<" original="<<v186_request
             <<" cpu="<<v186_cpu<<" sc="<<v186_sc<<std::endl;
    check(v186_ack&&v186_y2&&v186_irq&&v186_queued&&v186_consumed&&
          v186_request&&v186_cpu,
          "V186 native IOS service did not ACK genuine second SC Open request");
    ++v186_ack_seen;
    v185_target_pc=addr;v185_target_lr=ctx.lr;
    ++v185_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
NEXT_TRIAL='''       using V186Bus=undercover::wii::IosBus;
       using V186Mail=undercover::wii::IpcMailbox;
       using V186Irq=undercover::wii::HollywoodIrq;
       using V186Ios=undercover::wii::StmIos;
       const auto v186_ctrl=nwii::runtime::ipc70_bus.read32(
              V186Bus::IPC+V186Mail::PPCCTRL);
       const auto v186_flag=nwii::runtime::ipc70_bus.read32(
              V186Bus::IPC+V186Irq::PPC_FLAG);
       const bool v186_guest=nwii::runtime::v186_ack_seen==1u&&
              nwii::runtime::v185_next_seen==1u&&
              nwii::runtime::v184_burst_seen==1u&&
              c.pc==0x80529434u&&c.lr==0x80526cb0u&&!c.is_running;
       const bool v186_mail=v186_ctrl.has_value()&&v186_flag.has_value()&&
              ((*v186_ctrl&V186Mail::Y2)!=0u)&&
              ((*v186_ctrl&(V186Mail::X1|V186Mail::Y1))==0u)&&
              ((*v186_flag&V186Irq::IPC_PPC)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level();
       const bool v186_service=
              nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
              !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
              nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
              nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  V186Ios::Open&&
              c.mmu.read8(c.gpr[13]-3176u)==1u;
       std::cout<<"V186_ACK_STATE guest="<<v186_guest
                <<" mail="<<v186_mail<<" service="<<v186_service<<std::endl;
       check(v186_guest&&v186_mail&&v186_service,
             "V186 original second IOS_Open ACK did not leave valid guest boundary");'''

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V186 inherited owner-original V185 yield marker differs")
    s=once(s,STATE,STATE+'''
 static unsigned v186_ack_seen=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v186_ack_seen=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,HANDOFF,1))
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return once(s,V153_FIRST_REPLY_GUARD,V186_SCOPED_V153_GUARD)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
