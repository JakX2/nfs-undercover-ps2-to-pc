#!/usr/bin/env python3
"""V170 continue original SYSCONF Y1 reply processor beyond its MMIO read.

Owner-private V169 verified the original processor 0x805190C0 entered
control-read helper 0x8051905C with LR 0x805190E8, while the reply packet
and Y1 were valid and SC status at r13-3176 was 1. Run the authentic PPC
read helper, then observe the *next original guest call* with its real caller
and SDA byte. Do not assume it is a callback, force Y1 clear, set status,
create an IOS event, or write any PowerPC register/memory.
"""
import argparse
import re
from pathlib import Path
from derive_v169_sc_reply_processor_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    ++v169_next_seen;
    v169_target_pc=addr;v169_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051905cu&&ctx.lr==0x805190e8u,
          "V170 original SC reply processor IPC read ABI differs from V169");
    v170_start_inst=ctx.inst_count;
    ++v169_next_seen;
    v169_target_pc=addr;v169_target_lr=ctx.lr;
    return; // original guest IPC control-read instructions, no synthetic return
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v169_next_seen==1u&&v170_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto control=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool y1=control.has_value()&&((*control&Mail::Y1)!=0u);
    const bool irq=flag.has_value()&&((*flag&Irq::IPC_PPC)!=0u);
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool wire=arm.has_value()&&*arm==v153_phys;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v170_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=!(ctx.lr&3u);
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (!masked&&ipc70_bus.external_irq_level());
    const uint32_t sda=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sda)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sda):0u;
    const bool read=addr==0x8051905cu;
    const bool write=addr==0x8051906cu;
    std::cout<<"V170_SC_REPLY_READ_NEXT guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" y1="<<y1<<" irq="<<irq
             <<" reply="<<reply<<" wire="<<wire<<" status="<<status
             <<" read="<<read<<" write="<<write
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V170 original SC reply processor did not call authentic next guest function");
    ++v170_next_seen;
    v170_target_pc=addr;v170_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v169_target_pc&&'
    r'(?P<space>\s+)c\.lr==nwii::runtime::v169_target_lr')

NEXT_TRIAL='''       check(nwii::runtime::v170_next_seen==1u&&
             nwii::runtime::v169_next_seen==1u&&
             nwii::runtime::v168_next_seen==1u&&
             nwii::runtime::v167_next_seen==1u&&
             c.pc==nwii::runtime::v170_target_pc&&
             c.lr==nwii::runtime::v170_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V170 original SC reply read helper did not reach next native guest call");'''

def extend_prior_gates(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v169_target_pc&&'
                 'c.lr==nwii::runtime::v169_target_lr)||'
                 '(nwii::runtime::v170_next_seen==1u&&'
                 'c.pc==nwii::runtime::v170_target_pc&&'
                 'c.lr==nwii::runtime::v170_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 4<=count<=14:
        raise ValueError(f"V170 requires 4-14 prior original-PC guards, found {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V170 legacy original-path trial label changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        check=updated[start:end]
        if start<0 or end-start>2400 or "v170_next_seen==1u" not in check:
            raise ValueError(f"V170 prior original-path strict trial not extended: {label}")
    return updated

def once(source: str,old: str,new: str)->str:
    n=source.count(old)
    if n!=1:
        raise ValueError(f"V170 native source-only anchor count={n}: {old[:80]}")
    return source.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V170 inherited V169 reply-read boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v170_next_seen=0;
 static uint64_t v170_start_inst=0;
 static uint32_t v170_target_pc=0,v170_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v170_next_seen=0u;
     nwii::runtime::v170_start_inst=0u;
     nwii::runtime::v170_target_pc=nwii::runtime::v170_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return extend_prior_gates(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
