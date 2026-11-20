#!/usr/bin/env python3
"""V167 execute original Wii SC Y1 reply IPC handler to first native leaf.

V166 authenticated 0x80519318 with LR 0x80526CAC after second reply IRQ,
including intact SYSCONF IOS_Open response and pending Broadway Y1. Release
the original registered handler and record its first translated guest call.
Do not assume which branch the Y1 handler takes; distinguish read helpers
without faking IOS callbacks, PPC status, reply acknowledgments or execution.
"""
import argparse
from pathlib import Path
from derive_v166_sc_post_restore_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL, V166_FINAL,
    V166_CHECK, V166_TRIAL_END,
)
STOP='''    ++v166_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80519318u&&ctx.lr==0x80526cacu,
          "V167 authentic registered SC Y1 IPC handler call differs from V166");
    v167_start_inst=ctx.inst_count;
    ++v166_next_seen;
    return; // run original Y1 IPC interrupt handler guest code
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v166_next_seen==1u&&v167_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y1=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.inst_count>v167_start_inst&&ctx.pc==addr&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&
          !(ctx.lr&3u);
    const bool read=addr==0x8051905cu||addr==0x8051906cu;
    std::cout<<"V167_SC_REPLY_LEAF y1="<<y1<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked<<" caller="<<caller
             <<" read="<<read<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(y1&&reply&&guest&&masked&&caller,
          "V167 original SC Y1 IPC handler did not reach authentic first leaf");
    v167_target_pc=addr;v167_target_lr=ctx.lr;
    ++v167_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V167_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_leaf_seen==1u&&
               (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running,'''
V167_CHECK='''             ((c.pc==INT_DISABLE||c.pc==INT_RESTORE)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             !c.is_running,'''
V167_TRIAL_END='''             ((c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V166_LAST='''             c.pc==nwii::runtime::v166_target_pc&&
             c.lr==nwii::runtime::v166_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V167_LAST='''             ((c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v167_next_seen==1u&&
             nwii::runtime::v166_next_seen==1u&&
             nwii::runtime::v165_next_seen==1u&&
             nwii::runtime::v164_leaf_seen==1u&&
             c.pc==nwii::runtime::v167_target_pc&&
             c.lr==nwii::runtime::v167_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V167 original SC reply IPC handler did not reach first real guest leaf");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V167 original-free source anchor count={n}: {old[:76]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
        PREVIOUS_TRIAL.count(V166_LAST)!=1 or
        s.count(V166_FINAL)!=1 or s.count(V166_CHECK)!=1 or
        s.count(V166_TRIAL_END)!=1):
        raise ValueError("V167 inherited V166 authenticated IPC entry/checkpoints differ")
    s=once(s,STATE,STATE+'''
 static unsigned v167_next_seen=0;
 static uint64_t v167_start_inst=0;
 static uint32_t v167_target_pc=0,v167_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v167_next_seen=0u;
     nwii::runtime::v167_start_inst=0u;
     nwii::runtime::v167_target_pc=nwii::runtime::v167_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,V166_FINAL,V167_FINAL)
    s=once(s,V166_CHECK,V167_CHECK)
    s=once(s,V166_TRIAL_END,V167_TRIAL_END)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V166_LAST,V167_LAST,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
