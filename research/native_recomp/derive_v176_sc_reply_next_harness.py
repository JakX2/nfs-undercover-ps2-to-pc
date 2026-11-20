#!/usr/bin/env python3
"""V176 continue original Wii SYSCONF reply path beyond PC 0x805228CC.

V175 owner-original execution verified the next function call at 0x805228CC,
LR 0x80519298, with SC status byte r13-3176 still 1 and both IPC IRQ
acknowledgments complete. Run the unchanged translated guest instructions
and capture the next *actual* function call and status. The next target is
not guessed and no IOS service, callback, guest store or branch is inserted.
"""
import argparse
import re
from pathlib import Path
from derive_v175_sc_reply_next_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    v175_target_pc=addr;v175_target_lr=ctx.lr;
    ++v175_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805228ccu&&ctx.lr==0x80519298u,
          "V176 original SC reply next function differs from V175 owner run");
    const uint32_t v176_sc=ctx.gpr[13]-3176u;
    check(ctx.mmu.get_ptr(v176_sc)!=nullptr&&ctx.mmu.read8(v176_sc)==1u,
          "V176 inherited original SC SDA status differs from verified V175");
    v176_start_inst=ctx.inst_count;
    v176_sda_before=ctx.mmu.read8(v176_sc);
    v175_target_pc=addr;v175_target_lr=ctx.lr;
    ++v175_next_seen;
    return; // execute original Wii 0x805228CC function without host override
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v175_next_seen==1u&&v176_next_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v176_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=v176_sda_before;
    const bool osinit=addr==0x8052096cu;
    std::cout<<"V176_SC_REPLY_NEXT clean="<<clean<<" wire="<<wire
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v176_sda_before
             <<" status="<<status<<" changed="<<changed
             <<" osinit="<<osinit
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V176 original SYSCONF reply path did not reach a valid native call");
    v176_target_pc=addr;v176_target_lr=ctx.lr;
    ++v176_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v175_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v175_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v176_next_seen==1u&&
             nwii::runtime::v175_next_seen==1u&&
             nwii::runtime::v174_next_seen==1u&&
             nwii::runtime::v173_flag_ack_seen==1u&&
             c.pc==nwii::runtime::v176_target_pc&&
             c.lr==nwii::runtime::v176_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V176 original SC reply callback frontier did not enter next guest function");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V176 original-free derived harness anchor count={n}: {old[:72]}")
    return s.replace(old,new,1)

def widen_prior(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v175_target_pc&&'
                 'c.lr==nwii::runtime::v175_target_lr)||'
                 '(nwii::runtime::v176_next_seen==1u&&'
                 'c.pc==nwii::runtime::v176_target_pc&&'
                 'c.lr==nwii::runtime::v176_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 7<=n<=58:
        raise ValueError(f"V176 authenticated predecessor PC/LR gate count differs: {n}")
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
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V176 preceding authentic guest gate changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>5500 or "v176_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V176 earlier guest trial rejects authenticated next call: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V176 inherited original SC reply successor checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v176_next_seen=0;
 static uint64_t v176_start_inst=0;
 static uint32_t v176_sda_before=0;
 static uint32_t v176_target_pc=0,v176_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v176_next_seen=0u;
     nwii::runtime::v176_start_inst=0u;
     nwii::runtime::v176_sda_before=0u;
     nwii::runtime::v176_target_pc=nwii::runtime::v176_target_lr=0u;''')
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
