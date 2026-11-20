#!/usr/bin/env python3
"""V165 continue original second SC Y1 nested OSDI to next real guest call.

The independently verified V164 owner-original suite (16/16) reached
OSDisableInterrupts at 0x805265AC, LR 0x8052940C, from the authentic
second reply interrupt dispatcher. Release that specific nested guest call,
execute original PPC helper instructions, and record the next translated
guest function call with SYSCONF IOS_Open reply and Y1 IRQ still intact.
No new IOS service, forced return, guest writes, status-byte mutation,
synthetic callback or exception is introduced.
"""
import argparse
from pathlib import Path
from derive_v164_sc_y1_nested_helper_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    V164_FINAL
)

STOP='''    ++v164_leaf_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265acu&&ctx.lr==0x8052940cu,
          "V165 nested original OSDI guest function ABI differs from verified V164");
    v165_start_inst=ctx.inst_count;
    ++v164_leaf_seen;
    return; // execute authentic nested OSDisableInterrupts guest instructions
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v164_leaf_seen==1u&&v165_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v165_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool call=ctx.lr>=0x80526a3cu&&ctx.lr<0x80529434u&&
          !(ctx.lr&3u);
    const bool restore=addr==INT_RESTORE;
    std::cout<<"V165_SC_AFTER_OSDI irq="<<irq<<" reply="<<reply
             <<" guest="<<guest<<" masked="<<masked
             <<" call="<<call<<" restore="<<restore
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&guest&&masked&&call,
          "V165 original SC Y1 nested OSDI did not reach valid next guest call");
    ++v165_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V165_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_leaf_seen==1u&&
               (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc>=0x80400000u&&c.pc<0x80600000u&&
               c.lr>=0x80526a3cu&&c.lr<0x80529434u))&&
             !c.is_running,'''
V164_NEXT_PC='''             (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
             c.lr>=0x805293f8u&&c.lr<0x80529434u&&
             !c.is_running,'''
V165_NEXT_PC='''             (((c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc>=0x80400000u&&c.pc<0x80600000u&&
               c.lr>=0x80526a3cu&&c.lr<0x80529434u))&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v165_next_seen==1u&&
             nwii::runtime::v164_leaf_seen==1u&&
             nwii::runtime::v163_next_seen==1u&&
             nwii::runtime::v162_next_seen==1u&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             c.lr>=0x80526a3cu&&c.lr<0x80529434u&&
             !c.is_running,
             "V165 original second SC nested OSDI did not reach real guest successor");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V165 owner-free source anchor count={n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
        PREVIOUS_TRIAL.count(V164_NEXT_PC)!=1 or
        s.count(V164_FINAL)!=1):
        raise ValueError("V165 inherited verified V164 stop or trial differs")
    s=once(s,STATE,STATE+'''
 static unsigned v165_next_seen=0;
 static uint64_t v165_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v165_next_seen=0u;
     nwii::runtime::v165_start_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,V164_FINAL,V165_FINAL)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V164_NEXT_PC,V165_NEXT_PC,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
