#!/usr/bin/env python3
"""V194 execute authentic Wii OSRestoreInterrupts after verified V193.

V193 owner-original 16/16 passed at PC 0x805265D4, LR 0x8052F92C.
The real guest had just masked MSR.EE but did not clear Y2 or service the
second IOS_Open completion. Execute that original translated PowerPC
interrupt-restore routine and observe its next true function call with the
unmodified guest context, interrupt and pending IOS state.
"""
import argparse
import re
from pathlib import Path
from derive_v193_osdi_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v193_target_pc=addr;v193_target_lr=ctx.lr;
    v193_final_sc=sc;v193_final_queue=queue;
    ++v193_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265d4u&&ctx.lr==0x8052f92cu&&
          y2&&flagset&&queue&&guest&&coherent&&mapped&&caller&&
          sc==1u&&!ee&&!ready&&ctx.gpr[3]==1u&&!ctx.cr[0].eq,
          "V194 authentic Wii OSRestoreInterrupts entry or IRQ state differs");
    v193_target_pc=addr;v193_target_lr=ctx.lr;
    v193_final_sc=sc;v193_final_queue=queue;
    ++v193_next_seen;
    v194_start_inst=ctx.inst_count;
    return; // execute original Wii OSRestoreInterrupts
  }'''
OBSERVER='''  // V194 resumes the actual original OSRestoreInterrupts helper from
  // the authenticated V193 checkpoint. Do not force EE, dispatch the IRQ,
  // pump IOS, clear Y2, synthesize a reply, or set guest SC readiness.
  if(v193_next_seen==1u&&v192_next_seen==1u&&v194_next_seen==0u&&
     (addr==0x80000500u||addr==0x80000c00u||
      (addr>=0x80400000u&&addr<0x80600000u))){
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v194_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool caller=(ctx.lr&3u)==0u;
    const bool vector=addr==0x80000500u;
    std::cout<<"V194_RESTORE_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" coherent="<<coherent
             <<" mapped="<<mapped<<" caller="<<caller
             <<" sc="<<sc<<" ee="<<ee<<" ready="<<ready
             <<" vector="<<vector
             <<" r3="<<ctx.gpr[3]<<" eq="<<ctx.cr[0].eq
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(y2&&flagset&&queue&&request&&guest&&coherent&&
          mapped&&caller&&sc==1u,
          "V194 original Wii OSRestoreInterrupts next call did not preserve second IOS ACK");
    v194_target_pc=addr;v194_target_lr=ctx.lr;
    v194_final_sc=sc;v194_final_queue=queue;
    ++v194_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v193_target_pc&&\s*c\.lr==nwii::runtime::v193_target_lr')
NEXT_TRIAL='''       using V194Bus=undercover::wii::IosBus;
       using V194Ios=undercover::wii::StmIos;
       const bool v194_guest=nwii::runtime::v194_next_seen==1u&&
             nwii::runtime::v193_next_seen==1u&&
             nwii::runtime::v192_next_seen==1u&&
             c.pc==nwii::runtime::v194_target_pc&&
             c.lr==nwii::runtime::v194_target_lr&&
             (c.pc==0x80000500u||c.pc==0x80000c00u||
              (c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running;
       const bool v194_irq=nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V194Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v194_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v194_final_sc;
       const bool v194_queue=
             (nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
              !nwii::runtime::ipc70_bus.pending_native_ios_request())==
             nwii::runtime::v194_final_queue;
       const bool v194_open=nwii::runtime::ipc70_ram.valid(
                 nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(
                 nwii::runtime::v183_second_phys)==V194Ios::Open;
       std::cout<<"V194_RESTORE_STATE guest="<<v194_guest
                <<" irq="<<v194_irq<<" sc="<<v194_sc
                <<" queue="<<v194_queue<<" open="<<v194_open<<std::endl;
       check(v194_guest&&v194_irq&&v194_sc&&v194_queue&&v194_open,
             "V194 original Wii interrupt-restore successor state differs");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v193_target_pc&&'
                 'c.lr==nwii::runtime::v193_target_lr)||'
                 '(nwii::runtime::v194_next_seen==1u&&'
                 'c.pc==nwii::runtime::v194_target_pc&&'
                 'c.lr==nwii::runtime::v194_target_lr))')
    s,count=PAIR.subn(replacement,source)
    if not 7<=count<=420:
        raise ValueError(f"V194 previous exact PowerPC checkpoint count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if s.count(marker)!=1:
            raise ValueError(f"V194 original historical owner proof changed: {label}")
        end=s.index(marker);start=s.rfind("check(",0,end)
        if start<0 or end-start>30000 or "v194_next_seen==1u" not in s[start:end]:
            raise ValueError(f"V194 historical owner proof rejects original next PPC call: {label}")
    for begin in ("const bool v186_guest=","const bool v187_guest=",
                  "const bool v188_guest=","const bool v189_guest=",
                  "const bool v190_guest=","const bool v191_guest=",
                  "const bool v192_guest=","const bool v193_guest="):
        if s.count(begin)!=1:
            raise ValueError(f"V194 inherited predicate changed: {begin}")
        a=s.index(begin);b=s.index("const bool ",a+len(begin))
        if "v194_next_seen==1u" not in s[a:b]:
            raise ValueError(f"V194 inherited original guest predicate rejects next call: {begin}")
    return s

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V194 V193 original PPC end-of-function stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v194_next_seen=0u;
 static uint64_t v194_start_inst=0u;
 static uint32_t v194_target_pc=0u,v194_target_lr=0u,v194_final_sc=0u;
 static bool v194_final_queue=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v194_next_seen=0u;
     nwii::runtime::v194_start_inst=0u;
     nwii::runtime::v194_target_pc=nwii::runtime::v194_target_lr=nwii::runtime::v194_final_sc=0u;
     nwii::runtime::v194_final_queue=false;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+'\n'+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
