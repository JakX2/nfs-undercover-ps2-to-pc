#!/usr/bin/env python3
"""V167 execute real second SC Y1 IPC handler to first original leaf call.

V166 verified that original nested OSRestore reached registered IPC handler
0x80519318, LR 0x80526CAC, with the SYSCONF IOS_Open reply on ARMMSG/Y1.
Run original handler code to its first translated helper, with read-only
checks on reply ownership, masked IRQ and guest ABI. This does not clear
Y1, fabricate a callback or modify Wii PowerPC guest instructions.
"""
import argparse
from pathlib import Path
from derive_v166_sc_post_restore_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    V166_FINAL,V166_CHECK,V165_TRIAL_END as V165_OLD_TRIAL,
    V166_TRIAL_END as V166_OLD_TRIAL,
)

STOP='''    v166_target_pc=addr;v166_target_lr=ctx.lr;
    ++v166_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80519318u&&ctx.lr==0x80526cacu,
          "V167 second original SC Y1 IPC handler callsite differs from V166");
    v167_start_inst=ctx.inst_count;
    v166_target_pc=addr;v166_target_lr=ctx.lr;
    ++v166_next_seen;
    return; // run genuine PPC IPC reply-handler instructions
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v166_next_seen==1u&&v167_leaf_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v167_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&
          !(ctx.lr&3u);
    const bool leaf=addr==0x8051905cu||addr==0x8051906cu||
          addr==0x8051b060u;
    std::cout<<"V167_SC_Y1_LEAF y1="<<y1<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked
             <<" caller="<<caller<<" leaf="<<leaf
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(y1&&reply&&guest&&masked&&caller&&leaf,
          "V167 original SC reply IPC handler first guest helper differs");
    v167_target_pc=addr;v167_target_lr=ctx.lr;
    ++v167_leaf_seen;
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
              (nwii::runtime::v167_leaf_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             !c.is_running,'''
V167_CHECK='''             ((c.pc==INT_DISABLE||c.pc==INT_RESTORE)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_leaf_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             !c.is_running,'''
V167_V165_TRIAL='''             ((c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_leaf_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V166_TRIAL_END='''             c.pc==nwii::runtime::v166_target_pc&&
             c.lr==nwii::runtime::v166_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V167_V166_TRIAL='''             ((c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr)||
              (nwii::runtime::v167_leaf_seen==1u&&
               c.pc==nwii::runtime::v167_target_pc&&
               c.lr==nwii::runtime::v167_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v167_leaf_seen==1u&&
             nwii::runtime::v166_next_seen==1u&&
             nwii::runtime::v165_next_seen==1u&&
             nwii::runtime::v164_leaf_seen==1u&&
             c.pc==nwii::runtime::v167_target_pc&&
             c.lr==nwii::runtime::v167_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V167 authentic SC reply IPC handler did not reach first leaf");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V167 fail-closed derived harness anchor count={n}: {old[:74]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V166_TRIAL_END)!=1:
        raise ValueError("V167 inherited original second IPC handler stop differs")
    for anchor in (V166_FINAL,V166_CHECK,V166_OLD_TRIAL):
        if s.count(anchor)!=1:
            raise ValueError(f"V167 predecessor end-of-trial proof changed: {anchor[:65]}")
    s=once(s,STATE,STATE+'''
 static unsigned v167_leaf_seen=0;
 static uint64_t v167_start_inst=0;
 static uint32_t v167_target_pc=0,v167_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v167_leaf_seen=0u;
     nwii::runtime::v167_start_inst=0u;
     nwii::runtime::v167_target_pc=nwii::runtime::v167_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,V166_FINAL,V167_FINAL)
    s=once(s,V166_CHECK,V167_CHECK)
    s=once(s,V166_OLD_TRIAL,V167_V165_TRIAL)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V166_TRIAL_END,V167_V166_TRIAL,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
