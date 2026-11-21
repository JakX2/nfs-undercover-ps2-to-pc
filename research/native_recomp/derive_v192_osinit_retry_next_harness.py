#!/usr/bin/env python3
"""V192 continue the original Wii OSInit retry helper after authenticated V191.

V191 owner-original 16/16 passed in GitHub Actions run 44856455287:
PC=0x8052F830 LR=0x80520970 SC=1 MSR.EE=1 IRQ-ready=1,
with the second IOS_Open ACK and one unconsumed native completion queued.
Execute the *original* guest helper and observe whether it returns through
the retry loop, calls a different PPC routine or enters the exception
vector. Do not call IOS, synthesize replies, alter PC or change SC state.
"""
import argparse
import re
from pathlib import Path
from derive_v191_second_ios_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v191_target_pc=addr;v191_target_lr=ctx.lr;
    v191_final_sc=sc;
    ++v191_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    // V191 was authenticated at this exact original helper + IRQ state.
    check(addr==0x8052f830u&&ctx.lr==0x80520970u&&
          y2&&flagset&&queue&&request&&guest&&caller&&coherent&&mapped&&
          sc==1u&&ee&&ready,
          "V192 original V191 OSInit helper entry or IRQ state differed");
    v191_target_pc=addr;v191_target_lr=ctx.lr;
    v191_final_sc=sc;
    ++v191_next_seen;
    v192_start_inst=ctx.inst_count;
    return; // execute actual original Wii OSInit retry helper
  }'''
OBSERVER='''  // V192 continues actual original code at 0x8052F830. The next entry
  // could be a repeated OSInit retry, another helper or the real low-memory
  // external IRQ vector. Observe all possibilities without injecting one.
  if(v191_next_seen==1u&&v186_ack_seen==1u&&v192_next_seen==0u&&
     (addr==0x80000500u||addr==0x80000c00u||
      (addr>=0x80400000u&&addr<0x80600000u))){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y2=ctrl.has_value()&&((*ctrl&Mail::Y2)!=0u);
    const bool flagset=flags.has_value()&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool guest=ctx.pc==addr&&ctx.inst_count>v192_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool retry=addr==0x8052f830u&&ctx.lr==0x80520970u;
    const bool vector=addr==0x80000500u;
    const bool caller=(ctx.lr&3u)==0u;
    std::cout<<"V192_OSINIT_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" guest="<<guest
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" caller="<<caller<<" retry="<<retry<<" vector="<<vector
             <<" sc="<<sc<<" ee="<<ee<<" ready="<<ready
             <<" r3="<<ctx.gpr[3]<<" eq="<<ctx.cr[0].eq
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&coherent&&mapped&&caller,
          "V192 original OSInit retry helper did not reach subsequent PPC entry");
    v192_target_pc=addr;v192_target_lr=ctx.lr;
    v192_final_sc=sc;v192_final_queue=queue;
    ++v192_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v191_target_pc&&\s*c\.lr==nwii::runtime::v191_target_lr')
NEXT_TRIAL='''       using V192Bus=undercover::wii::IosBus;
       const bool v192_guest=nwii::runtime::v192_next_seen==1u&&
             nwii::runtime::v191_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             c.pc==nwii::runtime::v192_target_pc&&
             c.lr==nwii::runtime::v192_target_lr&&
             (c.pc==0x80000500u||c.pc==0x80000c00u||
              (c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running;
       const bool v192_irq=nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V192Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v192_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v192_final_sc;
       const bool v192_queue=
             (nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
              !nwii::runtime::ipc70_bus.pending_native_ios_request())==
             nwii::runtime::v192_final_queue;
       std::cout<<"V192_OSINIT_STATE guest="<<v192_guest
                <<" irq="<<v192_irq<<" sc="<<v192_sc
                <<" queue="<<v192_queue<<std::endl;
       check(v192_guest&&v192_irq&&v192_sc&&v192_queue,
             "V192 original Wii OSInit helper native next-call state differs");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v191_target_pc&&'
                 'c.lr==nwii::runtime::v191_target_lr)||'
                 '(nwii::runtime::v192_next_seen==1u&&'
                 'c.pc==nwii::runtime::v192_target_pc&&'
                 'c.lr==nwii::runtime::v192_target_lr))')
    s,count=PAIR.subn(replacement,source)
    if not 7<=count<=350:
        raise ValueError(f"V192 authenticated prior checkpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if s.count(marker)!=1:
            raise ValueError(f"V192 inherited owner guest proof changed: {label}")
        end=s.index(marker);start=s.rfind("check(",0,end)
        if start<0 or end-start>28000 or "v192_next_seen==1u" not in s[start:end]:
            raise ValueError(f"V192 historical guest proof cannot accept new call: {label}")
    for begin in ("const bool v186_guest=","const bool v187_guest=",
                  "const bool v188_guest=","const bool v189_guest=",
                  "const bool v190_guest=","const bool v191_guest="):
        if s.count(begin)!=1:
            raise ValueError(f"V192 inherited guest predicate differs: {begin}")
        a=s.index(begin);b=s.index("const bool ",a+len(begin))
        if "v192_next_seen==1u" not in s[a:b]:
            raise ValueError(f"V192 inherited owner guest predicate rejects next call: {begin}")
    return s

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V192 authenticated V191 original PPC stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v192_next_seen=0u;
 static uint64_t v192_start_inst=0u;
 static uint32_t v192_target_pc=0u,v192_target_lr=0u,v192_final_sc=0u;
 static bool v192_final_queue=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v192_next_seen=0u;
     nwii::runtime::v192_start_inst=0u;
     nwii::runtime::v192_target_pc=nwii::runtime::v192_target_lr=nwii::runtime::v192_final_sc=0u;
     nwii::runtime::v192_final_queue=false;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+'\n'+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
