#!/usr/bin/env python3
"""V171 run repeated original SC Y1 reply IPC reads until distinct callee.

V170 verified a second 0x8051905C call from LR 0x805190FC (SDA=1, Y1
asserted). Execute unchanged Wii PowerPC read helpers with a hard 32-call
budget. Stop at the first *different* real game function and report actual
reply, MMIO and SC status. Do not synthesize a callback, IRQ ACK, status
change, return instruction or IOS scheduler tick.
"""
import argparse
import re
from pathlib import Path
from derive_v170_sc_reply_read_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    ++v170_next_seen;
    v170_target_pc=addr;v170_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051905cu&&ctx.lr==0x805190fcu,
          "V171 original SC reply processor second IPC read callsite differs");
    v171_start_inst=ctx.inst_count;
    ++v170_next_seen;
    v170_target_pc=addr;v170_target_lr=ctx.lr;
    return; // execute original PPC read and allow future genuine calls
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v170_next_seen==1u&&v171_distinct_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool y1=ctrl.has_value()&&((*ctrl&Mail::Y1)!=0u);
    const bool irq=flag.has_value()&&((*flag&Irq::IPC_PPC)!=0u);
    const bool wire=arm.has_value()&&*arm==v153_phys;
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v171_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=1u;
    if(addr==0x8051905cu){
      ++v171_read_count;
      if(v171_read_count>32u){
        std::cout<<"V171_SC_READ_LIMIT count="<<v171_read_count<<std::endl;
        check(false,"V171 authentic SC Y1 read helper loop exceeded budget");
      }
      check(guest&&caller&&coherent&&mapped,
            "V171 repeated SC Y1 read lost native guest/MMIO invariants");
      v171_start_inst=ctx.inst_count;
      return; // perform another original PPC read, never synthesize its result
    }
    const bool write=addr==0x8051906cu;
    std::cout<<"V171_SC_DISTINCT guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" y1="<<y1<<" irq="<<irq<<" wire="<<wire
             <<" reply="<<reply<<" status="<<status
             <<" changed="<<changed<<" write="<<write
             <<" reads="<<v171_read_count
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped&&v171_read_count<=32u,
          "V171 original SC reply processor did not reach distinct guest helper");
    ++v171_distinct_seen;
    v171_target_pc=addr;v171_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_TRIAL='''       check(nwii::runtime::v171_distinct_seen==1u&&
             nwii::runtime::v170_next_seen==1u&&
             nwii::runtime::v169_next_seen==1u&&
             nwii::runtime::v168_next_seen==1u&&
             c.pc==nwii::runtime::v171_target_pc&&
             c.lr==nwii::runtime::v171_target_lr&&
             c.pc!=0x8051905cu&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V171 original SC reply processor did not reach distinct native callee");'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v170_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v170_target_lr')

def widen_prior_pc_gates(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v170_target_pc&&'
                 'c.lr==nwii::runtime::v170_target_lr)||'
                 '(nwii::runtime::v171_distinct_seen==1u&&'
                 'c.pc==nwii::runtime::v171_target_pc&&'
                 'c.lr==nwii::runtime::v171_target_lr))')
    updated,count=PAIR.subn(replacement,s)
    if not 6<=count<=20:
        raise ValueError(f"V171 expected 6..20 inherited PC/LR proofs, found {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V171 previous native trial assertion changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        segment=updated[start:end]
        if start<0 or end-start>2400 or "v171_distinct_seen==1u" not in segment:
            raise ValueError(f"V171 next guest PC/LR not accepted by prior checkpoint: {label}")
    return updated

def once(s: str,old: str,new: str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V171 original-free source anchor count={count}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V171 previous authentic second IPC read stop differs")
    s=once(s,STATE,STATE+'''
 static unsigned v171_read_count=0,v171_distinct_seen=0;
 static uint64_t v171_start_inst=0;
 static uint32_t v171_target_pc=0,v171_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v171_read_count=nwii::runtime::v171_distinct_seen=0u;
     nwii::runtime::v171_start_inst=0u;
     nwii::runtime::v171_target_pc=nwii::runtime::v171_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior_pc_gates(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
