#!/usr/bin/env python3
"""V193 native OSDisableInterrupts after verified original Wii OSInit retry call.

V192 authentic owner-native 16/16 reached PC=0x805265AC / LR=0x8052F84C
with SC=1, second IOS_Open completion queued and MSR.EE=1. Execute this
real PPC OSDisableInterrupts function, observe the next real guest call and
read hardware status without forcing IRQ/IOS progress or guest state.
"""
import argparse
import re
from pathlib import Path
from derive_v192_osinit_retry_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v192_target_pc=addr;v192_target_lr=ctx.lr;
    v192_final_sc=sc;v192_final_queue=queue;
    ++v192_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265acu&&ctx.lr==0x8052f84cu&&
          guest&&coherent&&mapped&&caller&&queue&&
          sc==1u&&ee&&ready&&ctx.gpr[3]==1u&&ctx.cr[0].eq,
          "V193 original Wii OSDisableInterrupts caller or pending IOS differs");
    v192_target_pc=addr;v192_target_lr=ctx.lr;
    v192_final_sc=sc;v192_final_queue=queue;
    ++v192_next_seen;
    v193_start_inst=ctx.inst_count;
    return; // execute original Wii OSDisableInterrupts helper
  }'''
OBSERVER='''  // Resume the genuine interrupt-disable helper from original OSInit.
  // Preserve all guest IRQ and IOS ownership; no synthetic context writes.
  if(v192_next_seen==1u&&v191_next_seen==1u&&v193_next_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v193_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool caller=(ctx.lr&3u)==0u;
    std::cout<<"V193_OSDI_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" guest="<<guest
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" caller="<<caller<<" sc="<<sc
             <<" ee="<<ee<<" ready="<<ready
             <<" r3="<<ctx.gpr[3]<<" eq="<<ctx.cr[0].eq
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&coherent&&mapped&&caller,
          "V193 original Wii interrupt-disable routine did not reach authentic next PPC call");
    v193_target_pc=addr;v193_target_lr=ctx.lr;
    v193_final_sc=sc;v193_final_queue=queue;
    ++v193_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v192_target_pc&&\s*c\.lr==nwii::runtime::v192_target_lr')
NEXT_TRIAL='''       using V193Bus=undercover::wii::IosBus;
       const bool v193_guest=nwii::runtime::v193_next_seen==1u&&
             nwii::runtime::v192_next_seen==1u&&
             nwii::runtime::v191_next_seen==1u&&
             c.pc==nwii::runtime::v193_target_pc&&
             c.lr==nwii::runtime::v193_target_lr&&
             (c.pc==0x80000500u||c.pc==0x80000c00u||
              (c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running;
       const bool v193_irq=nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V193Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v193_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v193_final_sc;
       const bool v193_queue=
             (nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
              !nwii::runtime::ipc70_bus.pending_native_ios_request())==
             nwii::runtime::v193_final_queue;
       std::cout<<"V193_OSDI_STATE guest="<<v193_guest
                <<" irq="<<v193_irq<<" sc="<<v193_sc
                <<" queue="<<v193_queue<<std::endl;
       check(v193_guest&&v193_irq&&v193_sc&&v193_queue,
             "V193 original Wii interrupt-disable successor state differs");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v192_target_pc&&'
                 'c.lr==nwii::runtime::v192_target_lr)||'
                 '(nwii::runtime::v193_next_seen==1u&&'
                 'c.pc==nwii::runtime::v193_target_pc&&'
                 'c.lr==nwii::runtime::v193_target_lr))')
    s,count=PAIR.subn(replacement,source)
    if not 7<=count<=380:
        raise ValueError(f"V193 prior authenticated checkpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if s.count(marker)!=1:
            raise ValueError(f"V193 inherited owner guest proof differs: {label}")
        end=s.index(marker);start=s.rfind("check(",0,end)
        if start<0 or end-start>30000 or "v193_next_seen==1u" not in s[start:end]:
            raise ValueError(f"V193 historical guest proof rejects authentic next call: {label}")
    for begin in ("const bool v186_guest=","const bool v187_guest=",
                  "const bool v188_guest=","const bool v189_guest=",
                  "const bool v190_guest=","const bool v191_guest=",
                  "const bool v192_guest="):
        if s.count(begin)!=1:
            raise ValueError(f"V193 inherited guest predicate changed: {begin}")
        a=s.index(begin);b=s.index("const bool ",a+len(begin))
        if "v193_next_seen==1u" not in s[a:b]:
            raise ValueError(f"V193 original guest predicate rejects next PPC call: {begin}")
    return s

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V193 original V192 native callback stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v193_next_seen=0u;
 static uint64_t v193_start_inst=0u;
 static uint32_t v193_target_pc=0u,v193_target_lr=0u,v193_final_sc=0u;
 static bool v193_final_queue=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v193_next_seen=0u;
     nwii::runtime::v193_start_inst=0u;
     nwii::runtime::v193_target_pc=nwii::runtime::v193_target_lr=nwii::runtime::v193_final_sc=0u;
     nwii::runtime::v193_final_queue=false;''')
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
