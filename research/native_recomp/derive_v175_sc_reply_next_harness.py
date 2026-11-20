#!/usr/bin/env python3
"""V175 execute original Wii SC reply function 0x80522AF4 into its next call.

The original owner V174 16-trial execution reached PC 0x80522AF4 with
LR 0x80519290, the native Y1/Hollywood IRQ acknowledgments both finished,
the original SYSCONF IOS_Open response intact, and r13-3176 still 1.
Run this function's original translated PowerPC body and record the next
guest entry and status-byte value, never inventing a callback or store.
"""
import argparse
import re
from pathlib import Path
from derive_v174_sc_post_reply_helper_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    v174_target_pc=addr;v174_target_lr=ctx.lr;
    ++v174_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80522af4u&&ctx.lr==0x80519290u,
          "V175 original SC reply successor callsite differs from V174");
    const uint32_t v175_sc=ctx.gpr[13]-3176u;
    check(ctx.mmu.get_ptr(v175_sc)!=nullptr&&ctx.mmu.read8(v175_sc)==1u,
          "V175 original SC status differs from verified V174 callback frontier");
    v175_start_inst=ctx.inst_count;
    v175_sda_before=ctx.mmu.read8(v175_sc);
    v174_target_pc=addr;v174_target_lr=ctx.lr;
    ++v174_next_seen;
    return; // execute the original 0x80522AF4 PowerPC function
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v174_next_seen==1u&&v175_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto control=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool clean=control.has_value()&&flags.has_value()&&
          ((*control&Mail::Y1)==0u)&&((*control&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool wire=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          arm.has_value()&&*arm==v153_phys;
    const bool queue=ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v175_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc):0u;
    const bool changed=mapped&&status!=v175_sda_before;
    std::cout<<"V175_SC_REPLY_NEXT clean="<<clean
             <<" wire="<<wire<<" queue="<<queue
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" before="<<v175_sda_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(clean&&guest&&caller&&coherent&&mapped,
          "V175 original SYSCONF reply successor did not reach authentic guest call");
    v175_target_pc=addr;v175_target_lr=ctx.lr;
    ++v175_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v174_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v174_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v175_next_seen==1u&&
             nwii::runtime::v174_next_seen==1u&&
             nwii::runtime::v173_next_seen==1u&&
             nwii::runtime::v173_flag_ack_seen==1u&&
             c.pc==nwii::runtime::v175_target_pc&&
             c.lr==nwii::runtime::v175_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V175 original SC reply successor did not reach new PPC callee");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V175 original-free guest checkpoint anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def widen_prior(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v174_target_pc&&'
                 'c.lr==nwii::runtime::v174_target_lr)||'
                 '(nwii::runtime::v175_next_seen==1u&&'
                 'c.pc==nwii::runtime::v175_target_pc&&'
                 'c.lr==nwii::runtime::v175_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 7<=n<=46:
        raise ValueError(f"V175 verified previous guest endpoint count changed: {n}")
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
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V175 inherited authentic guest gate changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        segment=updated[start:end]
        if start<0 or end-start>4800 or "v175_next_seen==1u" not in segment:
            raise ValueError(f"V175 older trial did not retain new native endpoint: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V175 original SC reply follow-up checkpoint no longer matches")
    s=once(s,STATE,STATE+'''
 static unsigned v175_next_seen=0;
 static uint64_t v175_start_inst=0;
 static uint32_t v175_sda_before=0;
 static uint32_t v175_target_pc=0,v175_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v175_next_seen=0u;
     nwii::runtime::v175_start_inst=0u;
     nwii::runtime::v175_sda_before=0u;
     nwii::runtime::v175_target_pc=nwii::runtime::v175_target_lr=0u;''')
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
