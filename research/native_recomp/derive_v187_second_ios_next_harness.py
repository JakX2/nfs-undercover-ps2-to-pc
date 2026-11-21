#!/usr/bin/env python3
"""V187 authentic original PowerPC scheduler successor after second IOS Open ACK.

The V186 owner-original runner proved 16/16 real Starlet Y2 acknowledgments
for the game's second IOS_Open, at PC 0x80529434 and LR 0x80526CB0.
Allow genuine original PPC execution to continue until its next text call.
No additional IOS pump, fabricated reply, IRQ dispatch, guest register write,
SC readiness mutation or proprietary translated code is introduced.
"""
import argparse
import re
from pathlib import Path
from derive_v186_second_ios_ack_harness import (
    derive as previous, STATE, RESET, HANDOFF as PREVIOUS_HANDOFF,
    NEXT_TRIAL as PREVIOUS_TRIAL,
    V186_SCOPED_V153_GUARD, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v186_ack_seen;
    v185_target_pc=addr;v185_target_lr=ctx.lr;
    ++v185_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80529434u&&ctx.lr==0x80526cb0u&&
          v186_route&&v186_prior&&v186_ack&&v186_y2&&v186_irq&&
          v186_queued&&v186_consumed&&v186_request&&v186_cpu&&
          v186_sc,
          "V187 authentic Y2-acknowledged scheduler entry was modified");
    ++v186_ack_seen;
    v185_target_pc=addr;v185_target_lr=ctx.lr;
    ++v185_next_seen;
    v187_start_inst=ctx.inst_count;
    return; // continue original Wii guest scheduler after native Starlet Y2 ACK
  }'''
OBSERVER='''  // V187: allow exactly one new original Wii PPC function-entry callback
  // following V186's genuine second IOS_Open Y2 acknowledgment.
  if(v186_ack_seen==1u&&v185_next_seen==1u&&v187_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y2=ctrl.has_value()&&((*ctrl&Mail::Y2)!=0u)&&
          ((*ctrl&(Mail::X1|Mail::Y1))==0u);
    const bool flagset=flag.has_value()&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool request=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v187_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool sc=mapped&&status==1u;
    std::cout<<"V187_SC_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" sc="<<sc<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(queue&&request&&guest&&caller&&coherent&&mapped&&sc,
          "V187 original guest scheduler successor lacks queued second IOS reply");
    v187_target_pc=addr;v187_target_lr=ctx.lr;
    ++v187_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V186_GUEST='''c.pc==0x80529434u&&c.lr==0x80526cb0u&&!c.is_running'''
V187_GUEST='''((c.pc==0x80529434u&&c.lr==0x80526cb0u)||
              (nwii::runtime::v187_next_seen==1u&&
               c.pc==nwii::runtime::v187_target_pc&&
               c.lr==nwii::runtime::v187_target_lr))&&!c.is_running'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v185_target_pc&&\s*c\.lr==nwii::runtime::v185_target_lr')
NEXT_TRIAL='''       using V187Bus=undercover::wii::IosBus;
       using V187Mail=undercover::wii::IpcMailbox;
       using V187Irq=undercover::wii::HollywoodIrq;
       using V187Ios=undercover::wii::StmIos;
       const auto v187_ctrl=nwii::runtime::ipc70_bus.read32(V187Bus::IPC+V187Mail::PPCCTRL);
       const auto v187_flag=nwii::runtime::ipc70_bus.read32(V187Bus::IPC+V187Irq::PPC_FLAG);
       const bool v187_guest=nwii::runtime::v187_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             nwii::runtime::v185_next_seen==1u&&
             c.pc==nwii::runtime::v187_target_pc&&
             c.lr==nwii::runtime::v187_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running;
       const bool v187_queue=
             nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
             !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
             nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  V187Ios::Open;
       const bool v187_irq=v187_ctrl.has_value()&&v187_flag.has_value()&&
             nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V187Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v187_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==1u;
       std::cout<<"V187_SC_STATE guest="<<v187_guest
                <<" queue="<<v187_queue<<" irq="<<v187_irq
                <<" sc="<<v187_sc<<std::endl;
       check(v187_guest&&v187_queue&&v187_irq&&v187_sc,
             "V187 original second ACK successor did not retain valid native IOS state");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v185_target_pc&&'
                 'c.lr==nwii::runtime::v185_target_lr)||'
                 '(nwii::runtime::v187_next_seen==1u&&'
                 'c.pc==nwii::runtime::v187_target_pc&&'
                 'c.lr==nwii::runtime::v187_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=220:
        raise ValueError(f"V187 historical native guest endpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
        "V178 original SC reply burst did not reach bounded native checkpoint",
        "V182 original SC reply call burst did not reach authenticated native stop",
        "V183 original SC reply IPC followup did not reach bounded guest call",
        "V184 original SC reply continuation did not enter bounded native call",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V187 inherited historical native assertion changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>15000 or "v187_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V187 historic guest guard would reject later successor: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_HANDOFF.count(STOP)!=1:
        raise ValueError("V187 original V186 callback stop no longer authentic")
    if V186_SCOPED_V153_GUARD.count(V186_GUEST)!=1:
        raise ValueError("V187 inherited first-SC reply guard differs")
    if PREVIOUS_TRIAL.count(V186_GUEST)!=1:
        raise ValueError("V187 inherited second-SC ACK guest gate differs")
    s=once(s,STATE,STATE+'''
 static unsigned v187_next_seen=0u;
 static uint64_t v187_start_inst=0u;
 static uint32_t v187_target_pc=0u,v187_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v187_next_seen=0u;
     nwii::runtime::v187_start_inst=0u;
     nwii::runtime::v187_target_pc=nwii::runtime::v187_target_lr=0u;''')
    s=once(s,PREVIOUS_HANDOFF,PREVIOUS_HANDOFF.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL.replace(V186_GUEST,V187_GUEST,1)+'\n'+NEXT_TRIAL)
    s=once(s,V186_SCOPED_V153_GUARD,
           V186_SCOPED_V153_GUARD.replace(V186_GUEST,V187_GUEST,1))
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
