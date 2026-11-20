#!/usr/bin/env python3
"""V168 execute the original second SYSCONF Y1 IPC control-read helper.

The owner-original V167 run proved that the second Y1 handler calls
0x8051905C with LR 0x8051933C, unlike the first Y2 handler's read site.
Release only that authenticated stop and observe the next original call
owned by the IPC handler. The original PPC code, IOS reply and hardware
Y1/IPC interrupt state are preserved. Do not assume the following target.
"""
import argparse
from pathlib import Path
from derive_v167_sc_reply_leaf_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, TRACE_ANCHOR,
    V167_FINAL, V167_CHECK, V167_TRIAL_END, V167_LAST,
)

STOP='''    v167_target_pc=addr;v167_target_lr=ctx.lr;
    ++v167_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051905cu&&ctx.lr==0x8051933cu,
          "V168 original SC reply read-helper caller differs from V167 proof");
    v168_start_inst=ctx.inst_count;
    v167_target_pc=addr;v167_target_lr=ctx.lr;
    ++v167_next_seen;
    return; // execute the original PPC control-read helper
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v167_next_seen==1u&&v168_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool y1=ctrl.has_value()&&flags.has_value()&&arm.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)!=0u)&&*arm==v153_phys&&
          ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v168_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=!(ctx.lr&3u);
    const bool read=addr==0x8051905cu;
    const bool write=addr==0x8051906cu;
    std::cout<<"V168_SC_REPLY_NEXT y1="<<y1<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked
             <<" caller="<<caller<<" read="<<read<<" write="<<write
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(y1&&reply&&guest&&masked&&caller,
          "V168 original SC Y1 control-read did not reach valid next handler call");
    v168_target_pc=addr;v168_target_lr=ctx.lr;
    ++v168_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''

def widen(s: str, marker: str, addition: str)->str:
    if s.count(marker)!=1:
        raise ValueError("V168 terminal predicate insertion is not unique")
    return s.replace(marker,addition+marker,1)

V168_FINAL=widen(V167_FINAL,
    '''))&&
             !c.is_running,''',
    '''||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u)''')
V168_CHECK=widen(V167_CHECK,
    '''))&&
             !c.is_running,''',
    '''||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr)''')
V168_TRIAL_END=widen(V167_TRIAL_END,
    '''))&&
             c.pc>=0x80400000u''',
    '''||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr)''')
V168_LAST=widen(V167_LAST,
    '''))&&
             c.pc>=0x80400000u''',
    '''||
              (nwii::runtime::v168_next_seen==1u&&
               c.pc==nwii::runtime::v168_target_pc&&
               c.lr==nwii::runtime::v168_target_lr)''')
NEXT_TRIAL='''       check(nwii::runtime::v168_next_seen==1u&&
             nwii::runtime::v167_next_seen==1u&&
             nwii::runtime::v166_next_seen==1u&&
             nwii::runtime::v165_next_seen==1u&&
             c.pc==nwii::runtime::v168_target_pc&&
             c.lr==nwii::runtime::v168_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V168 authentic SC Y1 reply read helper did not advance to next guest call");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V168 original-free anchor count={n}: {old[:72]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V167_LAST)!=1:
        raise ValueError("V168 inherited original Y1 reply leaf checkpoint differs")
    for anchor in (V167_FINAL,V167_CHECK,V167_TRIAL_END):
        if s.count(anchor)!=1:
            raise ValueError(f"V168 inherited terminal predicate changed: {anchor[:70]}")
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
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
