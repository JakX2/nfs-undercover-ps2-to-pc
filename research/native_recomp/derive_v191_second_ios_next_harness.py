#!/usr/bin/env python3
"""V191 native Wii context helper: resume authentic V190 PPC rescheduler successor.

V190 owner-original CI 44852816608 passed 16/16 trials, reaching original
PC 0x805229B4 with LR 0x80526CBC after the second IOS_Open ACK.
Execute this original guest function to its next native PPC entry. Merely
observe IOS Y2, interrupt, SC status, and guest ABI; never synthesize replies,
write guest state or schedule extra IOS steps. Proprietary originals stay private.
"""
import argparse
import re
from pathlib import Path
from derive_v190_second_ios_resched_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v190_target_pc=addr;v190_target_lr=ctx.lr;
    ++v190_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805229b4u&&ctx.lr==0x80526cbcu&&
          queue&&request&&guest&&caller&&coherent&&mapped&&sc&&
          y2&&flagset&&!ee&&!ready,
          "V191 original V190 PPC context callee differs from verified endpoint");
    v190_target_pc=addr;v190_target_lr=ctx.lr;
    ++v190_next_seen;
    v191_start_inst=ctx.inst_count;
    return; // execute original Wii PPC context helper
  }'''
OBSERVER='''  // V191 resumes the exact V190 owner-original PC/LR without modifying
  // guest context, memory, IOS services, reply scheduling, or interrupt state.
  if(v190_next_seen==1u&&v186_ack_seen==1u&&v191_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y2=ctrl.has_value()&&((*ctrl&Mail::Y2)!=0u);
    const bool flagset=flags.has_value()&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool request=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v191_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(sc_addr):0u;
    std::cout<<"V191_SC_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" sc="<<sc<<" ee="<<ee<<" ready="<<ready
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    // The V191 owner-original 16-trial trace authenticated this exact
    // return to OSInit, with interrupts enabled but second Y2 still pending.
    check(y2&&flagset&&queue&&request&&guest&&caller&&coherent&&mapped&&
          sc==1u&&ee&&ready&&addr==0x8052f830u&&ctx.lr==0x80520970u,
          "V191 authentic Wii OSInit retry helper or IRQ state differed");
    v191_target_pc=addr;v191_target_lr=ctx.lr;
    v191_final_sc=sc;
    ++v191_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v190_target_pc&&\s*c\.lr==nwii::runtime::v190_target_lr')
NEXT_TRIAL='''       using V191Bus=undercover::wii::IosBus;
       using V191Ios=undercover::wii::StmIos;
       const bool v191_guest=nwii::runtime::v191_next_seen==1u&&
             nwii::runtime::v190_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             c.pc==nwii::runtime::v191_target_pc&&
             c.lr==nwii::runtime::v191_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running;
       const bool v191_queue=
             nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
             !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
             nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==V191Ios::Open;
       const bool v191_irq=nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V191Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v191_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v191_final_sc;
       std::cout<<"V191_SC_STATE guest="<<v191_guest<<" queue="<<v191_queue
                <<" irq="<<v191_irq<<" sc="<<v191_sc<<std::endl;
       check(v191_guest&&v191_queue&&v191_irq&&v191_sc,
             "V191 original Wii context helper failed to preserve pending second IOS state");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v190_target_pc&&'
                 'c.lr==nwii::runtime::v190_target_lr)||'
                 '(nwii::runtime::v191_next_seen==1u&&'
                 'c.pc==nwii::runtime::v191_target_pc&&'
                 'c.lr==nwii::runtime::v191_target_lr))')
    s,count=PAIR.subn(replacement,source)
    if not 7<=count<=300:
        raise ValueError(f"V191 authenticated prior checkpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if s.count(marker)!=1:
            raise ValueError(f"V191 inherited original guest assertion changed: {label}")
        end=s.index(marker);start=s.rfind("check(",0,end)
        if start<0 or end-start>25000 or "v191_next_seen==1u" not in s[start:end]:
            raise ValueError(f"V191 prior owner guest proof rejects new checkpoint: {label}")
    if s.count('"V190 original Wii rescheduler did not retain second IOS IPC state");')!=1:
        raise ValueError("V191 original V190 IPC state guard missing")
    for begin in ("const bool v186_guest=","const bool v187_guest=",
                  "const bool v188_guest=","const bool v189_guest=",
                  "const bool v190_guest="):
        if s.count(begin)!=1:
            raise ValueError(f"V191 inherited guest predicate count differs: {begin}")
        a=s.index(begin);b=s.index("const bool ",a+len(begin))
        if "v191_next_seen==1u" not in s[a:b]:
            raise ValueError(f"V191 historic owner guest validation rejects new PPC target: {begin}")
    return s

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V191 real V190 owner-original PC/LR stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v191_next_seen=0u;
 static uint64_t v191_start_inst=0u;
 static uint32_t v191_target_pc=0u,v191_target_lr=0u,v191_final_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v191_next_seen=0u;
     nwii::runtime::v191_start_inst=0u;
     nwii::runtime::v191_target_pc=nwii::runtime::v191_target_lr=nwii::runtime::v191_final_sc=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+'\n'+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
