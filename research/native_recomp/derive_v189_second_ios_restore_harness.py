#!/usr/bin/env python3
"""V189 execute original Wii interrupt restore after second IOS Open Y2 ACK.

V188 owner-original verified 0x805265D4 / LR 0x80529458 after real PPC
interrupt disable, pending Starlet Y2, and one queued IOS completion.
Execute actual original instructions, capture MSR.EE and interrupt readiness,
then stop at the next real PPC call. No extra host IOS step or fake reply.
"""
import argparse
import re
from pathlib import Path
from derive_v188_second_ios_osdi_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v188_target_pc=addr;v188_target_lr=ctx.lr;
    ++v188_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265d4u&&ctx.lr==0x80529458u&&
          y2&&flagset&&queue&&request&&guest&&caller&&masked&&
          coherent&&mapped&&sc,
          "V189 genuine second-Y2-acknowledged Wii restore helper entry differs");
    v188_target_pc=addr;v188_target_lr=ctx.lr;
    ++v188_next_seen;
    v189_start_inst=ctx.inst_count;
    return; // execute original Wii interrupt-restore PowerPC instructions
  }'''
OBSERVER='''  // V189 observes the first original guest call after restoring the
  // interrupt state. Record MSR.EE rather than assigning a hypothetical value.
  if(v188_next_seen==1u&&v186_ack_seen==1u&&v189_next_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v189_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(sc_addr)==1u;
    std::cout<<"V189_SC_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" sc="<<sc<<" ee="<<ee<<" ready="<<ready
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(queue&&request&&guest&&caller&&coherent&&mapped&&sc,
          "V189 original Wii restore-interrupt helper did not reach valid second IOS successor");
    v189_target_pc=addr;v189_target_lr=ctx.lr;
    ++v189_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
OLD_V188_CHECK='''check(v188_guest&&v188_queue&&v188_irq&&v188_masked&&v188_sc,
             "V188 original second ACK interrupt-disable successor left invalid native state");'''
V189_SCOPED_CHECK='''check(v188_guest&&v188_queue&&v188_irq&&
             (v188_masked||nwii::runtime::v189_next_seen==1u)&&v188_sc,
             "V188 original second ACK interrupt-disable successor left invalid native state");'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v188_target_pc&&\s*c\.lr==nwii::runtime::v188_target_lr')
NEXT_TRIAL='''       using V189Bus=undercover::wii::IosBus;
       using V189Mail=undercover::wii::IpcMailbox;
       using V189Irq=undercover::wii::HollywoodIrq;
       using V189Ios=undercover::wii::StmIos;
       const auto v189_ctrl=nwii::runtime::ipc70_bus.read32(V189Bus::IPC+V189Mail::PPCCTRL);
       const auto v189_flags=nwii::runtime::ipc70_bus.read32(V189Bus::IPC+V189Irq::PPC_FLAG);
       const bool v189_guest=nwii::runtime::v189_next_seen==1u&&
             nwii::runtime::v188_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             c.pc==nwii::runtime::v189_target_pc&&
             c.lr==nwii::runtime::v189_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running;
       const bool v189_queue=
             nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
             !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
             nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  V189Ios::Open;
       const bool v189_irq=v189_ctrl.has_value()&&v189_flags.has_value()&&
             nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V189Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v189_ee=(c.msr&V189Bus::MSR_EE)!=0u;
       const bool v189_ready=nwii::runtime::ipc70_bus.external_exception_pending(c.msr);
       const bool v189_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==1u;
       std::cout<<"V189_SC_STATE guest="<<v189_guest
                <<" queue="<<v189_queue<<" irq="<<v189_irq
                <<" sc="<<v189_sc<<" ee="<<v189_ee
                <<" ready="<<v189_ready<<std::endl;
       check(v189_guest&&v189_queue&&v189_irq&&v189_sc,
             "V189 second IOS ACK original interrupt-restore guest state inconsistent");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v188_target_pc&&'
                 'c.lr==nwii::runtime::v188_target_lr)||'
                 '(nwii::runtime::v189_next_seen==1u&&'
                 'c.pc==nwii::runtime::v189_target_pc&&'
                 'c.lr==nwii::runtime::v189_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=260:
        raise ValueError(f"V189 inherited original PPC stop count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V182 original SC reply call burst did not reach authenticated native stop",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V189 prior original native guard changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>18000 or "v189_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V189 old guest end point would reject successor: {label}")
    for begin,end in (
        ("const bool v186_guest=","const bool v186_mail="),
        ("const bool v187_guest=","const bool v187_queue="),
        ("const bool v188_guest=","const bool v188_queue="),
    ):
        if updated.count(begin)!=1 or updated.count(end)!=1:
            raise ValueError(f"V189 inherited guest predicate changed: {begin}")
        i=updated.index(begin);j=updated.index(end,i)
        if "v189_next_seen==1u" not in updated[i:j]:
            raise ValueError(f"V189 earlier computed guest predicate cannot accept new target: {begin}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V189 inherited owner V188 restore call stop changed")
    if PREVIOUS_TRIAL.count(OLD_V188_CHECK)!=1:
        raise ValueError("V189 inherited historical masked MSR.EE proof changed")
    s=once(s,STATE,STATE+'''
 static unsigned v189_next_seen=0u;
 static uint64_t v189_start_inst=0u;
 static uint32_t v189_target_pc=0u,v189_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v189_next_seen=0u;
     nwii::runtime::v189_start_inst=0u;
     nwii::runtime::v189_target_pc=nwii::runtime::v189_target_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL.replace(OLD_V188_CHECK,V189_SCOPED_CHECK,1)+'\n'+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
