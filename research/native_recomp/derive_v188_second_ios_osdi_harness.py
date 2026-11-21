#!/usr/bin/env python3
"""V188 continue actual Wii OSDI called by scheduler after second IOS Y2 ACK.

V187 owner-original verified PC 0x805265AC / LR 0x80529448 with a real
pending second Starlet Y2 acknowledgment, IRQ and single IOS completion.
Execute the translated PowerPC interrupt-disable helper and observe the next
original guest call. No guest mutation, fake reply or extra IOS service step.
"""
import argparse
import re
from pathlib import Path
from derive_v187_second_ios_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v187_target_pc=addr;v187_target_lr=ctx.lr;
    ++v187_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265acu&&ctx.lr==0x80529448u&&
          y2&&flagset&&queue&&request&&guest&&caller&&coherent&&mapped&&sc,
          "V188 original second IOS Y2 scheduler OSDI entry was modified");
    v187_target_pc=addr;v187_target_lr=ctx.lr;
    ++v187_next_seen;
    v188_start_inst=ctx.inst_count;
    return; // execute original Wii interrupt-disable helper 0x805265AC
  }'''
OBSERVER='''  // V188 follows the original PPC interrupt-disable helper from V187.
  if(v187_next_seen==1u&&v186_ack_seen==1u&&v188_next_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v188_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(sc_addr)==1u;
    std::cout<<"V188_SC_NEXT y2="<<y2<<" flag="<<flagset
             <<" queue="<<queue<<" request="<<request
             <<" guest="<<guest<<" caller="<<caller
             <<" masked="<<masked<<" coherent="<<coherent
             <<" mapped="<<mapped<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(queue&&request&&guest&&caller&&masked&&coherent&&mapped&&sc,
          "V188 genuine second IOS ACK interrupt-disable did not reach native PPC successor");
    v188_target_pc=addr;v188_target_lr=ctx.lr;
    ++v188_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(r'c\.pc==nwii::runtime::v187_target_pc&&\s*c\.lr==nwii::runtime::v187_target_lr')
NEXT_TRIAL='''       using V188Bus=undercover::wii::IosBus;
       using V188Mail=undercover::wii::IpcMailbox;
       using V188Irq=undercover::wii::HollywoodIrq;
       using V188Ios=undercover::wii::StmIos;
       const auto v188_ctrl=nwii::runtime::ipc70_bus.read32(V188Bus::IPC+V188Mail::PPCCTRL);
       const auto v188_flag=nwii::runtime::ipc70_bus.read32(V188Bus::IPC+V188Irq::PPC_FLAG);
       const bool v188_guest=nwii::runtime::v188_next_seen==1u&&
             nwii::runtime::v187_next_seen==1u&&
             nwii::runtime::v186_ack_seen==1u&&
             c.pc==nwii::runtime::v188_target_pc&&
             c.lr==nwii::runtime::v188_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running;
       const bool v188_queue=
             nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
             !nwii::runtime::ipc70_bus.pending_native_ios_request()&&
             nwii::runtime::ipc70_ram.valid(nwii::runtime::v183_second_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  V188Ios::Open;
       const bool v188_irq=v188_ctrl.has_value()&&v188_flag.has_value()&&
             nwii::runtime::ipc70_bus.external_exception_pending(c.msr)==
             (((c.msr&V188Bus::MSR_EE)!=0u)&&
              nwii::runtime::ipc70_bus.external_irq_level());
       const bool v188_masked=(c.msr&V188Bus::MSR_EE)==0u;
       const bool v188_sc=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
             c.mmu.read8(c.gpr[13]-3176u)==1u;
       std::cout<<"V188_SC_STATE guest="<<v188_guest
                <<" queue="<<v188_queue<<" irq="<<v188_irq
                <<" masked="<<v188_masked<<" sc="<<v188_sc<<std::endl;
       check(v188_guest&&v188_queue&&v188_irq&&v188_masked&&v188_sc,
             "V188 original second ACK interrupt-disable successor left invalid native state");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v187_target_pc&&'
                 'c.lr==nwii::runtime::v187_target_lr)||'
                 '(nwii::runtime::v188_next_seen==1u&&'
                 'c.pc==nwii::runtime::v188_target_pc&&'
                 'c.lr==nwii::runtime::v188_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=250:
        raise ValueError(f"V188 inherited PPC stop assertion count changed: {count}")
    for label in (
        "V171 original SC reply processor did not reach distinct native callee",
        "V182 original SC reply call burst did not reach authenticated native stop",
        "V185 original IPC Y1 reader did not reach authentic native successor",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V188 original historical PPC guard label differs: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>16000 or "v188_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V188 earlier original proof rejects successor: {label}")
    # V186/V187 validate a computed v*_guest predicate, not an inline
    # PC/LR comparison in their final check() call. Verify the definition
    # itself includes the authenticated V188 endpoint.
    for begin,end in (
        ("const bool v186_guest=","const bool v186_mail="),
        ("const bool v187_guest=","const bool v187_queue="),
    ):
        if updated.count(begin)!=1 or updated.count(end)!=1:
            raise ValueError(f"V188 inherited variable guest predicate changed: {begin}")
        i=updated.index(begin);j=updated.index(end,i)
        if "v188_next_seen==1u" not in updated[i:j]:
            raise ValueError(f"V188 inherited variable guest predicate rejects new stop: {begin}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V188 authenticated V187 OSDI stop differs")
    s=once(s,STATE,STATE+'''
 static unsigned v188_next_seen=0u;
 static uint64_t v188_start_inst=0u;
 static uint32_t v188_target_pc=0u,v188_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v188_next_seen=0u;
     nwii::runtime::v188_start_inst=0u;
     nwii::runtime::v188_target_pc=nwii::runtime::v188_target_lr=0u;''')
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
