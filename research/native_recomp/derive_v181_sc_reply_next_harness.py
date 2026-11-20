#!/usr/bin/env python3
"""V181 continue a repeated original Wii allocator-related reply helper.

V180 owner-original execution verified 0x8051AD38 from LR 0x80519874,
clean IOS reply, and the still-unchanged SC status byte. Continue that PPC
callee, observing only the next original guest call and native SDA state.
Never fake the readiness byte, write guest state, or expose owner code.
"""
import argparse
import re
from pathlib import Path
from derive_v180_sc_reply_next_harness import (
    derive as previous, STATE, RESET, FOLLOWUP as PREVIOUS_FOLLOWUP,
    NEXT_TRIAL as PREVIOUS_TRIAL, OBSERVER_HEADER, once,
)

STOP='''    v180_target_pc=addr;v180_target_lr=ctx.lr;
    ++v180_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051ad38u&&ctx.lr==0x80519874u&&
          clean&&reply&&queue&&guest&&caller&&coherent&&mapped&&
          v180_status_before==1u&&status==1u&&!changed,
          "V181 original SC reply repeated allocator helper differs from V180");
    v181_start_inst=ctx.inst_count;
    v181_status_before=status;
    v180_target_pc=addr;v180_target_lr=ctx.lr;
    ++v180_next_seen;
    return; // execute authentic second 0x8051AD38 guest call
  }'''
FOLLOWUP='''  if(v180_next_seen==1u&&v181_next_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v181_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=v181_status_before;
    std::cout<<"V181_SC_NEXT clean="<<clean<<" reply="<<reply
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v181_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V181 original SYSCONF reply guest continuation lacks authentic next call");
    v181_target_pc=addr;v181_target_lr=ctx.lr;
    ++v181_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v180_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v180_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v181_next_seen==1u&&
             nwii::runtime::v180_next_seen==1u&&
             nwii::runtime::v178_burst_seen==1u&&
             nwii::runtime::v178_calls==6u&&
             c.pc==nwii::runtime::v181_target_pc&&
             c.lr==nwii::runtime::v181_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V181 original SC reply successor did not reach another native function");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v180_target_pc&&'
                 'c.lr==nwii::runtime::v180_target_lr)||'
                 '(nwii::runtime::v181_next_seen==1u&&'
                 'c.pc==nwii::runtime::v181_target_pc&&'
                 'c.lr==nwii::runtime::v181_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=130:
        raise ValueError(f"V181 inherited owner endpoint count changed: {count}")
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
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V181 inherited original guest assertion changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>10000 or "v181_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V181 inherited guest path rejects authentic next checkpoint: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_FOLLOWUP.count(STOP)!=1:
        raise ValueError("V181 inherited owner-original V180 call checkpoint differs")
    s=once(s,STATE,STATE+'''
 static unsigned v181_next_seen=0u;
 static uint64_t v181_start_inst=0u;
 static uint32_t v181_status_before=0u;
 static uint32_t v181_target_pc=0u,v181_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v181_next_seen=0u;
     nwii::runtime::v181_start_inst=0u;
     nwii::runtime::v181_status_before=0u;
     nwii::runtime::v181_target_pc=nwii::runtime::v181_target_lr=0u;''')
    s=once(s,PREVIOUS_FOLLOWUP,PREVIOUS_FOLLOWUP.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+FOLLOWUP)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
