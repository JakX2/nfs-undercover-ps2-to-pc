#!/usr/bin/env python3
"""V177 execute authentic SYSCONF reply guest callee at 0x804F0E04.

V176 owner-original Wii execution reached function 0x804F0E04 from the
SC reply-side handler at LR 0x805192AC. The pending IOS_Open reply remains
mapped, IPC Y1 and Hollywood flags are cleared, and SDA byte r13-3176 is 1.
Execute this original translated function and observe the next actual call
and SC state without inventing guest code, callback or hardware transitions.
"""
import argparse
import re
from pathlib import Path
from derive_v176_sc_reply_next_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    v176_target_pc=addr;v176_target_lr=ctx.lr;
    ++v176_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x804f0e04u&&ctx.lr==0x805192acu,
          "V177 original SYSCONF reply callee entry differs from V176 proof");
    const uint32_t v177_sc=ctx.gpr[13]-3176u;
    check(ctx.mmu.get_ptr(v177_sc)!=nullptr&&ctx.mmu.read8(v177_sc)==1u,
          "V177 inherited original SDA status differs from V176");
    v177_start_inst=ctx.inst_count;
    v177_sda_before=ctx.mmu.read8(v177_sc);
    v176_target_pc=addr;v176_target_lr=ctx.lr;
    ++v176_next_seen;
    return; // execute original 0x804F0E04 PowerPC body
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v176_next_seen==1u&&v177_next_seen==0u&&
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
    const bool wire=arm.has_value()&&*arm==v153_phys&&
          ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool queue=ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v177_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=v177_sda_before;
    const bool ipc=ctx.lr>=0x805190c0u&&ctx.lr<0x805194c4u;
    std::cout<<"V177_SC_REPLY_NEXT clean="<<clean<<" wire="<<wire
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v177_sda_before
             <<" status="<<status<<" changed="<<changed
             <<" ipc="<<ipc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V177 original SYSCONF reply callee did not reach valid guest successor");
    v177_target_pc=addr;v177_target_lr=ctx.lr;
    ++v177_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v176_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v176_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v177_next_seen==1u&&
             nwii::runtime::v176_next_seen==1u&&
             nwii::runtime::v175_next_seen==1u&&
             nwii::runtime::v174_next_seen==1u&&
             c.pc==nwii::runtime::v177_target_pc&&
             c.lr==nwii::runtime::v177_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V177 original SC reply handler callee did not enter subsequent native function");'''

def once(s: str, old: str, new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V177 original-free source anchor count={n}: {old[:72]}")
    return s.replace(old,new,1)

def widen_prior(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v176_target_pc&&'
                 'c.lr==nwii::runtime::v176_target_lr)||'
                 '(nwii::runtime::v177_next_seen==1u&&'
                 'c.pc==nwii::runtime::v177_target_pc&&'
                 'c.lr==nwii::runtime::v177_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 7<=n<=68:
        raise ValueError(f"V177 prior native PC/LR gate count changed: {n}")
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
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V177 previous guest assertion changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>6200 or "v177_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V177 inherited guest source proof rejects verified continuation: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V177 inherited guest 0x804F0E04 checkpoint differs")
    s=once(s,STATE,STATE+'''
 static unsigned v177_next_seen=0;
 static uint64_t v177_start_inst=0;
 static uint32_t v177_sda_before=0;
 static uint32_t v177_target_pc=0,v177_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v177_next_seen=0u;
     nwii::runtime::v177_start_inst=0u;
     nwii::runtime::v177_sda_before=0u;
     nwii::runtime::v177_target_pc=nwii::runtime::v177_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
