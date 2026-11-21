#!/usr/bin/env python3
"""V190 execute original Wii rescheduler after second IOS_Open ACK and OSRestore.

V189 owner-original reached PC 0x80529940/LR 0x80526CB4, EE still zero,
Y2 asserted, Hollywood IRQ and one queued second IOS completion. Execute
the real rescheduler to a new PPC function and observe its original CPU,
mailbox and SC state, without forced thread-selection or extra IOS steps.
"""
import argparse
import re
from pathlib import Path
from derive_v189_second_ios_restore_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v189_target_pc=addr;v189_target_lr=ctx.lr;
    ++v189_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80529940u&&ctx.lr==0x80526cb4u&&
          y2&&flagset&&queue&&request&&guest&&caller&&coherent&&mapped&&sc&&
          !ee&&!ready,
          "V190 authentic second IOS request rescheduler caller differs");
    v189_target_pc=addr;v189_target_lr=ctx.lr;
    ++v189_next_seen;
    v190_start_inst=ctx.inst_count;
    return; // execute authentic original Wii rescheduler function
  }'''
OBSERVER='''  // V190 executes the authentic PowerPC rescheduler from the V189
  // owner-original checkpoint; do not fabricate a thread-selection call.
  if(v189_next_seen==1u&&v186_ack_seen==1u&&v190_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y2=ctrl.has_value()&&((*ctrl&Mail::Y2)!=0u)&&
          ((*ctrl&(Mail::X1|Mail::Y1))==0u);
    const bool flagset=flags.has_value()&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool request=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v190_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(sc_addr)==1u;
    std::cout<<"V190_SC_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" sc="<<sc<<" ee="<<ee<<" ready="<<ready
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(queue&&request&&guest&&caller&&coherent&&mapped&&sc,
          "V190 original Wii rescheduler failed to reach real second IOS successor");
    v190_target_pc=addr;v190_target_lr=ctx.lr;
    ++v190_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V95_TITLE_PHASE='''   if(post95_active&&!submit72_active&&post94_query==1u){'''
V190_SCOPED_TITLE_PHASE='''   // V95 title-query allocator callbacks are valid only in the original
   // title-query phase. The V189 owner-original checkpoint proves the later
   // second-IOS rescheduler has reached its own authentic execution phase.
   // Preserve the V95 guard completely until that exact guest boundary.
   if(post95_active&&!submit72_active&&post94_query==1u&&
      !(v189_next_seen==1u&&v186_ack_seen==1u&&
        v189_target_pc==0x80529940u&&v189_target_lr==0x80526cb4u&&
        v190_next_seen==0u)){'''
V95_ALLOCATOR_ASSERT='''check(open71_profile==0u,"V95 duplicate allocator wrapper");'''
V190_V95_DIAGNOSTIC='''if(open71_profile!=0u){
          const bool v190_phase=v189_next_seen==1u;
          const bool v190_auth=v186_ack_seen==1u;
          const bool v190_target=v189_target_pc==0x80529940u&&
                v189_target_lr==0x80526cb4u;
          const bool v190_call=ctx.inst_count>v190_start_inst;
          std::cout<<"V190_V95_DUP phase="<<v190_phase
                   <<" auth="<<v190_auth<<" target="<<v190_target
                   <<" call="<<v190_call
                   <<" first="<<(post95_active&&post94_query==1u)
                   <<std::endl;
        }
        check(open71_profile==0u,"V95 duplicate allocator wrapper");'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v189_target_pc&&\s*c\.lr==nwii::runtime::v189_target_lr')
NEXT_TRIAL='''       using V190Bus=undercover::wii::IosBus;
       using V190Irq=undercover::wii::HollywoodIrq;
       using V190Ios=undercover::wii::StmIos;
       const bool v190_guest=nwii::runtime::v190_next_seen==1u&&
             nwii::runtime::v189_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             c.pc==nwii::runtime::v190_target_pc&&
             c.lr==nwii::runtime::v190_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running;
       const bool v190_queue=
             nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
             !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
             nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==V190Ios::Open;
       const bool v190_irq=nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V190Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v190_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==1u;
       std::cout<<"V190_SC_STATE guest="<<v190_guest<<" queue="<<v190_queue
                <<" irq="<<v190_irq<<" sc="<<v190_sc<<std::endl;
       check(v190_guest&&v190_queue&&v190_irq&&v190_sc,
             "V190 original Wii rescheduler did not retain second IOS IPC state");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v189_target_pc&&'
                 'c.lr==nwii::runtime::v189_target_lr)||'
                 '(nwii::runtime::v190_next_seen==1u&&'
                 'c.pc==nwii::runtime::v190_target_pc&&'
                 'c.lr==nwii::runtime::v190_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=270:
        raise ValueError(f"V190 original historical PC/LR endpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V182 original SC reply call burst did not reach authenticated native stop",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V190 historical owner assertion changed: {label}")
        end=updated.index(marker);start=updated.rfind("check(",0,end)
        if start<0 or end-start>18000 or "v190_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V190 original guest end point rejects real new call: {label}")
    for begin,end in (
        ("const bool v186_guest=","const bool v186_mail="),
        ("const bool v187_guest=","const bool v187_queue="),
        ("const bool v188_guest=","const bool v188_queue="),
        ("const bool v189_guest=","const bool v189_queue="),
    ):
        if updated.count(begin)!=1 or updated.count(end)!=1:
            raise ValueError(f"V190 historical guest computed predicate changed: {begin}")
        a=updated.index(begin);b=updated.index(end,a)
        if "v190_next_seen==1u" not in updated[a:b]:
            raise ValueError(f"V190 historical PPC guest predicate cannot accept new call: {begin}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V190 inherited V189 original rescheduler stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v190_next_seen=0u;
 static uint64_t v190_start_inst=0u;
 static uint32_t v190_target_pc=0u,v190_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v190_next_seen=0u;
     nwii::runtime::v190_start_inst=0u;
     nwii::runtime::v190_target_pc=nwii::runtime::v190_target_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+'\n'+NEXT_TRIAL)
    return once(once(widen_prior(s),V95_TITLE_PHASE,V190_SCOPED_TITLE_PHASE),
                V95_ALLOCATOR_ASSERT,V190_V95_DIAGNOSTIC)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
