#!/usr/bin/env python3
"""V160 execute original Broadway external exception vector after SC Y1 entry.

V159 admits an authentic, pending SC IOS_Open reply IRQ through the tested
native hardware exception bridge, stopping at 0x80000500. Release that stop
and run the installed *original Wii vector instructions* until the original
external interrupt handler entry 0x80526CE0. No replacement guest branch,
IRQ delivery, IOS pump, or callback state is introduced.
"""
import argparse
from pathlib import Path
from derive_v159_sc_y1_vector_harness import (
    derive as previous, STATE, RESET, CONTINUE as V159_CONTINUE,
    NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    ++v159_vector_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v160_start_inst=ctx.inst_count;
    ++v159_vector_seen;
    return true; // allow native dispatcher to execute original installed vector
  }'''
TRACE_ANCHOR="void trace_call(uint32_t addr, CPUContext&ctx){"
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v159_vector_seen==1u&&v160_handler_seen==0u){
    if(addr==undercover::wii::ExternalVector){
      const bool saved=ctx.srr0==v158_expected_pc&&
            ctx.srr1==(v158_expected_msr&undercover::wii::ExternalSrr1Mask);
      const bool regs=ctx.gpr==v158_expected_gprs&&
            ctx.lr==v158_expected_lr&&ctx.ctr==v158_expected_ctr&&
            ctx.xer==v158_expected_xer;
      bool bytes=true;
      for(size_t i=0;i<irq74_vector.size();++i)
        bytes&=ctx.mmu.read8(undercover::wii::ExternalVector+uint32_t(i))==
               irq74_vector[i];
      const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
      std::cout<<"V160_SC_VECTOR_ENTRY saved="<<saved
               <<" regs="<<regs<<" bytes="<<bytes
               <<" masked="<<masked<<std::endl;
      check(saved&&regs&&bytes&&masked,
            "V160 SC reply vector did not preserve installed PPC exception image");
      ++v160_vector_seen;
      return; // allow original guest exception vector instructions to run
    }
    if(addr==0x80526ce0u){
      // SRR0/SRR1 were authenticated at vector entry; original PPC vector
      // instructions may update them before entering the C exception body.
      const bool vector=v160_vector_seen==1u&&ctx.pc==addr;
      const bool index=ctx.gpr[3]==4u;
      const bool thread=ctx.gpr[4]==THREAD;
      const bool idle=ctx.gpr[4]==IDLE_CONTEXT;
      const bool abi=index&&(thread||idle);
      const bool sr0=ctx.srr0==v158_expected_pc;
      const bool sr1=ctx.srr1==
            (v158_expected_msr&undercover::wii::ExternalSrr1Mask);
      const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u&&
            !ipc70_bus.external_exception_pending(ctx.msr);
      const bool irq=ipc70_bus.external_irq_level()&&
            (ipc70_bus.read32(undercover::wii::IosBus::IPC+
                    undercover::wii::IpcMailbox::PPCCTRL).value_or(0u)&
                    undercover::wii::IpcMailbox::Y1)!=0u;
      const bool advanced=ctx.inst_count>v160_start_inst&&ctx.pc==addr;
      std::cout<<"V160_SC_VECTOR_ABI index="<<index
               <<" thread="<<thread<<" idle="<<idle
               <<" sr0="<<sr0<<" sr1="<<sr1<<std::endl;
      std::cout<<"V160_SC_VECTOR_HANDLER vector="<<vector
               <<" masked="<<masked<<" irq="<<irq
               <<" advanced="<<advanced
               <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
      check(vector&&abi&&masked&&irq&&advanced,
            "V160 original installed SC external vector did not reach handler");
      ++v160_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
'''
V159_PC='''             c.pc==undercover::wii::ExternalVector&&'''
V160_PC='''             (c.pc==undercover::wii::ExternalVector||
              (nwii::runtime::v160_handler_seen==1u&&
               c.pc==0x80526ce0u))&&'''
NEXT_TRIAL='''       check(nwii::runtime::v160_vector_seen==1u&&
             nwii::runtime::v160_handler_seen==1u&&
             nwii::runtime::v159_vector_seen==1u&&
             nwii::runtime::v158_rfi_seen==1u&&
             c.pc==0x80526ce0u&&
             c.srr0==nwii::runtime::v158_expected_pc&&
             !c.is_running,
             "V160 did not execute original SC Y1 exception vector to handler");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V160 original-free source anchor count={n}: {old[:68]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if V159_CONTINUE.count(STOP)!=1 or PREVIOUS_TRIAL.count(V159_PC)!=1:
        raise ValueError("V160 inherited authenticated reply IRQ vector differs")
    s=once(s,STATE,STATE+'''
 static unsigned v160_vector_seen=0,v160_handler_seen=0;
 static uint64_t v160_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v160_vector_seen=nwii::runtime::v160_handler_seen=0u;
     nwii::runtime::v160_start_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,TRACE)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V159_PC,V160_PC,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
