#!/usr/bin/env python3
"""V174 execute original SC Y1 reply successor 0x80522294, not a fake callback.

The owner-native V173 trace after authenticated Y1 and Hollywood PPC_FLAG
W1C reached 0x80522294, LR 0x80519124, with SYSCONF IOS_Open intact
and SDA status byte r13-3176 still 1. Resume this original translated
guest function and observe its first subsequent native function entry.
Read both SC byte values, IRQ hardware and IOS result without editing them.
No fabricated callback, PPC instruction, guest register, IOS step or store.
"""
import argparse
import re
from pathlib import Path
from derive_v173_sc_after_y1_ack_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    ++v173_flag_ack_seen;
    v173_target_pc=addr;v173_target_lr=ctx.lr;
    ++v173_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80522294u&&ctx.lr==0x80519124u,
          "V174 original second SC reply follow-up call differs from V173");
    const uint32_t sc=ctx.gpr[13]-3176u;
    check(ctx.mmu.get_ptr(sc)!=nullptr&&ctx.mmu.read8(sc)==1u,
          "V174 original SC SDA status no longer matches verified V173 state");
    v174_start_inst=ctx.inst_count;
    v174_sda_before=ctx.mmu.read8(sc);
    ++v173_flag_ack_seen;
    v173_target_pc=addr;v173_target_lr=ctx.lr;
    ++v173_next_seen;
    return; // execute original 0x80522294 PowerPC function unchanged
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v173_next_seen==1u&&v174_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool cleared=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&Mail::Y1)==0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          arm.has_value()&&*arm==v153_phys&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v174_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc):0u;
    const bool changed=mapped&&status!=v174_sda_before;
    std::cout<<"V174_SC_POST_REPLY_HELPER cleared="<<cleared
             <<" reply="<<reply<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v174_sda_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(cleared&&guest&&caller&&coherent&&mapped,
          "V174 SC reply function 0x80522294 did not reach valid original callee");
    v174_target_pc=addr;v174_target_lr=ctx.lr;
    ++v174_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v173_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v173_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v174_next_seen==1u&&
             nwii::runtime::v173_next_seen==1u&&
             nwii::runtime::v173_flag_ack_seen==1u&&
             nwii::runtime::v172_ack_seen==1u&&
             c.pc==nwii::runtime::v174_target_pc&&
             c.lr==nwii::runtime::v174_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V174 original Wii SC reply follow-up did not call next native helper");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V174 original-free guest source anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def widen_prior(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v173_target_pc&&'
                 'c.lr==nwii::runtime::v173_target_lr)||'
                 '(nwii::runtime::v174_next_seen==1u&&'
                 'c.pc==nwii::runtime::v174_target_pc&&'
                 'c.lr==nwii::runtime::v174_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 6<=n<=38:
        raise ValueError(f"V174 authenticated Y1 endpoint count changed: {n}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
        "V171 original SC reply processor did not reach distinct native callee",
        "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
        "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V174 prior checked original function changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        segment=updated[start:end]
        if start<0 or end-start>4200 or "v174_next_seen==1u" not in segment:
            raise ValueError(f"V174 previous guest checkpoint rejected new PC: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V174 inherited authenticated Hollywood ACK checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v174_next_seen=0;
 static uint64_t v174_start_inst=0;
 static uint32_t v174_sda_before=0;
 static uint32_t v174_target_pc=0,v174_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v174_next_seen=0u;
     nwii::runtime::v174_start_inst=0u;
     nwii::runtime::v174_sda_before=0u;
     nwii::runtime::v174_target_pc=nwii::runtime::v174_target_lr=0u;''')
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
