#!/usr/bin/env python3
"""V162 follow original SC Y1 IRQ dispatcher to its first genuine guest call.

V161 authenticated the second IOS reply interrupt's original dispatcher
at 0x80526A3C. Run this original PPC function until its next translated
function entry, preserving the pending IOS SYSCONF reply and Y1 MMIO state.
The synthetic owner test's *first* IRQ observers must not assert at the
second dispatcher's reused helper calls. No guest PC/register writes,
fabricated reply, forced callback, or original function body changes.
"""
import argparse
from pathlib import Path
from derive_v161_sc_y1_dispatch_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, V161_PC, V161_FINAL_PC,
)
STOP='''    ++v161_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v161_dispatch_seen;
    v162_dispatch_inst=ctx.inst_count;
    return; // execute the original second IRQ dispatcher
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v161_dispatch_seen==1u&&v162_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v162_dispatch_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x80526a3cu&&ctx.lr<0x80526ce0u&&
          !(ctx.lr&3u);
    std::cout<<"V162_SC_REPLY_NEXT irq="<<irq<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked
             <<" caller="<<caller<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&guest&&masked&&caller,
          "V162 original second SC interrupt dispatcher call lost reply or guest ABI");
    ++v162_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
OLDER_V76='''     if(irq76_dispatch){
       if(addr==0x8052a824u){'''
SCOPED_V76='''     if(irq76_dispatch&&v161_dispatch_seen==0u){
       if(addr==0x8052a824u){'''
OLDER_V143='''   if(v141_live && v142_dispatch_seen==1u && addr==0x8052a824u){'''
SCOPED_V143='''   if(v141_live && v142_dispatch_seen==1u &&
      v161_dispatch_seen==0u && addr==0x8052a824u){'''
V162_PC='''             (c.pc==undercover::wii::ExternalVector||
              (nwii::runtime::v160_handler_seen==1u&&
               c.pc==0x80526ce0u)||
              (nwii::runtime::v161_dispatch_seen==1u&&
               c.pc==0x80526a3cu)||
              (nwii::runtime::v162_next_seen==1u&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&'''
V162_FINAL_PC='''             (c.pc==0x80526a3cu||
              (nwii::runtime::v162_next_seen==1u&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&!c.is_running,'''
V161_NEXT_PC='''             c.pc==0x80526a3cu&&!c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v162_next_seen==1u&&
             nwii::runtime::v161_dispatch_seen==1u&&
             nwii::runtime::v160_handler_seen==1u&&
             nwii::runtime::v159_vector_seen==1u&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V162 original second SC IRQ dispatcher did not call genuine guest helper");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V162 original-free anchor count={n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_TRIAL.count(V161_NEXT_PC)!=1:
        raise ValueError('V162 V161 final trial PC gate changed')
    for pattern in (STOP,OLDER_V76,OLDER_V143,V161_PC,V161_FINAL_PC):
        if s.count(pattern)!=1:
            raise ValueError(f"V162 inherited IRQ observer differs: {pattern[:65]}")
    s=once(s,STATE,STATE+'''
 static unsigned v162_next_seen=0;
 static uint64_t v162_dispatch_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v162_next_seen=0u;
     nwii::runtime::v162_dispatch_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,OLDER_V76,SCOPED_V76)
    s=once(s,OLDER_V143,SCOPED_V143)
    s=once(s,V161_PC,V162_PC)
    s=once(s,V161_FINAL_PC,V162_FINAL_PC)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V161_NEXT_PC,V162_FINAL_PC,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
