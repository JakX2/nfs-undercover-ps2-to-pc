#!/usr/bin/env python3
"""V168 run original second SC Y1 IPC register-read helper to next guest call.

V167 proved the original IPC Y1 reply handler invokes register-read helper
0x8051905C with LR 0x8051933C. Execute that exact translated original
function, then observe the next real game callee. Keep IOS_Open response,
the Y1/IPC mailbox and masked PowerPC interrupt state intact. No synthetic
PPC return, MMIO acknowledge, SC callback or readiness-bit write.
"""
import argparse
from pathlib import Path
from derive_v167_sc_reply_leaf_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    V167_FINAL, V167_CHECK, V167_TRIAL_END,
)
STOP='''    ++v167_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051905cu&&ctx.lr==0x8051933cu,
          "V168 authentic Y1 IPC register-read helper callsite differs from V167");
    ++v167_next_seen;
    v168_start_inst=ctx.inst_count;
    return; // run original Wii IPC register-read guest instructions
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v167_next_seen==1u&&v168_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y1=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v168_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&
          !(ctx.lr&3u);
    const bool read=addr==0x8051905cu||addr==0x8051906cu;
    const bool other=addr!=v167_target_pc||ctx.lr!=v167_target_lr;
    std::cout<<"V168_SC_REPLY_NEXT y1="<<y1<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked<<" caller="<<caller
             <<" read="<<read<<" other="<<other
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(y1&&reply&&guest&&masked&&caller&&other,
          "V168 original Y1 IPC read helper did not reach a new guest call");
    v168_target_pc=addr;v168_target_lr=ctx.lr;
    ++v168_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V168_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
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
               c.pc>=0x80400000u&&c.pc<0x80600000u)||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running,'''
V168_CHECK='''             ((c.pc==INT_DISABLE||c.pc==INT_RESTORE)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr)||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr))&&
             !c.is_running,'''
V168_TRIAL_END='''             ((c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_next_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr)||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V167_LAST='''             c.pc==nwii::runtime::v167_target_pc&&
             c.lr==nwii::runtime::v167_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V168_LAST='''             ((c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr)||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v168_next_seen==1u&&
             nwii::runtime::v167_next_seen==1u&&
             nwii::runtime::v166_next_seen==1u&&
             nwii::runtime::v165_next_seen==1u&&
             c.pc==nwii::runtime::v168_target_pc&&
             c.lr==nwii::runtime::v168_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V168 original SC Y1 register read did not reach second guest leaf");'''

def once(s: str,old: str,new: str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V168 source anchor count={count}: {old[:76]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
        PREVIOUS_TRIAL.count(V167_LAST)!=1 or
        s.count(V167_FINAL)!=1 or s.count(V167_CHECK)!=1 or
        s.count(V167_TRIAL_END)!=1):
        raise ValueError("V168 inherited original SC Y1 read checkpoint differs")
    s=once(s,STATE,STATE+'''
 static unsigned v168_next_seen=0;
 static uint64_t v168_start_inst=0;
 static uint32_t v168_target_pc=0,v168_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v168_next_seen=0u;
     nwii::runtime::v168_start_inst=0u;
     nwii::runtime::v168_target_pc=nwii::runtime::v168_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,V167_FINAL,V168_FINAL)
    s=once(s,V167_CHECK,V168_CHECK)
    s=once(s,V167_TRIAL_END,V168_TRIAL_END)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V167_LAST,V168_LAST,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
