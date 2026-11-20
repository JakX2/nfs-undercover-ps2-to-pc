#!/usr/bin/env python3
"""V183 bounded original Wii native SC reply continuation from 0x8051906C.

V182 owner-original verified eight native call entries and returned the next
real function entry 0x8051906C from LR 0x80519780, retaining the actual IOS
reply and SC status r13-3176 == 1. Continue the translated Wii PowerPC code
through up to eight more original function entries; stop sooner if the real
SC byte changes. This is only source-owned observation, not guest mutation,
forced IOS completion, status fabrication, or a host callback.
"""
import argparse
import re
from pathlib import Path
from derive_v182_sc_reply_burst_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, OBSERVER_HEADER, once,
)

MAX_CALLS=8
# Owner-original V183 encountered the historical V77 IRQ dispatcher
# catch-all after verified V182. Log only source-owned phase/callsite flags
# without relaxing any earlier real IRQ dispatcher assertions.
V77_IRQ_CATCHALL='''check(false,"unexpected original IRQ dispatcher dependency");'''
V183_IRQ_DIAGNOSTIC='''{ // Preserve fail-fast and report bounded original-phase callsite only.
       const bool phase=v182_burst_seen==1u&&v183_burst_seen==0u;
       const bool submitted=submit72_active;
       const bool dispatcher=irq76_dispatch!=0u;
       const bool ipc=irq76_ipc!=0u;
       const bool prior=v177_next_seen==1u;
       const bool tracked=ctx.gpr[13]==v147_first_r13;
       const bool masked=(ctx.msr&0x8000u)==0u;
       const bool mapped=ctx.mmu.get_ptr(ctx.gpr[13]-3176u)!=nullptr;
       const unsigned sc=mapped?ctx.mmu.read8(ctx.gpr[13]-3176u):0u;
       std::cout<<"V183_IRQ_DEP phase="<<phase
                <<" submit="<<submitted<<" dispatch="<<dispatcher
                <<" ipc="<<ipc<<" prior="<<prior
                <<" tracked="<<tracked<<" masked="<<masked
                <<" mapped="<<mapped<<" status="<<sc
                <<" calls="<<v183_calls
                <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
                <<std::dec<<std::endl;
       check(false,"unexpected original IRQ dispatcher dependency");
     }'''

STOP='''    v182_target_pc=addr;v182_target_lr=ctx.lr;
    v182_final_status=status;
    ++v182_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051906cu&&ctx.lr==0x80519780u&&
          v182_calls==8u&&v182_status_before==1u&&
          clean&&reply&&queue&&guest&&caller&&coherent&&mapped&&
          status==1u&&!changed,
          "V183 authenticated original V182 IPC sender callee differs");
    v183_start_inst=ctx.inst_count;
    v183_last_inst=ctx.inst_count;
    v183_status_before=status;
    v182_target_pc=addr;v182_target_lr=ctx.lr;
    v182_final_status=status;
    ++v182_burst_seen;
    return; // execute original Wii 0x8051906C and bounded native callees
  }'''
OBSERVER='''  if(v182_burst_seen==1u&&v183_burst_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool clean=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)==0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool reply=arm.has_value()&&*arm==v153_phys&&
          ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool queue=ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v183_last_inst&&
          ctx.inst_count>v183_start_inst&&ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    check(guest&&caller&&coherent&&mapped&&v183_calls<8u,
          "V183 authenticated native SC reply call budget or guest ABI invalid");
    v183_trace_pc[v183_calls]=addr;
    v183_trace_lr[v183_calls]=ctx.lr;
    ++v183_calls;
    v183_last_inst=ctx.inst_count;
    const bool changed=status!=v183_status_before;
    if(v183_calls<8u&&!changed)
      return; // continue genuine guest code, no synthesized operations
    for(unsigned i=0u;i<v183_calls;++i)
      std::cout<<"V183_SC_TRACE step="<<(i+1u)
               <<" pc="<<std::hex<<v183_trace_pc[i]
               <<" lr="<<v183_trace_lr[i]<<std::dec<<std::endl;
    std::cout<<"V183_SC_BURST calls="<<v183_calls
             <<" clean="<<clean<<" reply="<<reply
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v183_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    v183_target_pc=addr;v183_target_lr=ctx.lr;
    v183_final_status=status;
    ++v183_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v182_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v182_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v183_burst_seen==1u&&
             nwii::runtime::v182_burst_seen==1u&&
             nwii::runtime::v182_calls==8u&&
             nwii::runtime::v181_next_seen==1u&&
             nwii::runtime::v183_calls>=1u&&
             nwii::runtime::v183_calls<=8u&&
             c.pc==nwii::runtime::v183_target_pc&&
             c.lr==nwii::runtime::v183_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V183 original SC reply IPC followup did not reach bounded guest call");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v182_target_pc&&'
                 'c.lr==nwii::runtime::v182_target_lr)||'
                 '(nwii::runtime::v183_burst_seen==1u&&'
                 'c.pc==nwii::runtime::v183_target_pc&&'
                 'c.lr==nwii::runtime::v183_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=160:
        raise ValueError(f"V183 inherited native PC/LR endpoint count changed: {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
        "V171 original SC reply processor did not reach distinct native callee",
        "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
        "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
        "V174 original Wii SC reply follow-up did not call next native helper",
        "V175 original SC reply successor did not reach new PPC callee",
        "V176 original SC reply callback frontier did not enter next guest function",
        "V177 original SC reply handler callee did not enter subsequent native function",
        "V178 original SC reply burst did not reach bounded native checkpoint",
        "V179 original SC reply continuation did not enter next PPC callee",
        "V180 original SC reply successor did not reach another native function",
        "V181 original SC reply successor did not reach another native function",
        "V182 original SC reply call burst did not reach authenticated native stop",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V183 prior native call milestone changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>13000 or "v183_burst_seen==1u" not in updated[start:end]:
            raise ValueError(f"V183 prior original check rejects new native guest stop: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    s=once(s,V77_IRQ_CATCHALL,V183_IRQ_DIAGNOSTIC)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V183 inherited V182 original guest stop differs")
    s=once(s,STATE,STATE+'''
 static unsigned v183_calls=0u,v183_burst_seen=0u;
 static uint64_t v183_start_inst=0u,v183_last_inst=0u;
 static uint32_t v183_status_before=0u,v183_final_status=0u;
 static uint32_t v183_target_pc=0u,v183_target_lr=0u;
 static std::array<uint32_t,8> v183_trace_pc{},v183_trace_lr{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v183_calls=nwii::runtime::v183_burst_seen=0u;
     nwii::runtime::v183_start_inst=nwii::runtime::v183_last_inst=0u;
     nwii::runtime::v183_status_before=nwii::runtime::v183_final_status=0u;
     nwii::runtime::v183_target_pc=nwii::runtime::v183_target_lr=0u;
     nwii::runtime::v183_trace_pc.fill(0u);
     nwii::runtime::v183_trace_lr.fill(0u);''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
