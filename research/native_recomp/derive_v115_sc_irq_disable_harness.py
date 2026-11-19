#!/usr/bin/env python3
"""V115 run the owner-original SC request cache syscall through its genuine vector and observe IRQ-disable entry."""
import argparse
from pathlib import Path
from derive_v114_sc_flush_syscall_harness import derive as previous

EDITS = [
    ("POST_OWNER=0x805222e8u", "POST_OWNER=0x805265acu"),
    (" static uint64_t post114_before=0;",
     " static uint64_t post114_before=0;\n static unsigned post115_vector=0,post115_sc=0,post115_disable=0;\n static bool post115_vector_active=false;"),
    ("if(v114_owner&&post113_flush==1u&&ctx.pc==POST_OWNER&&ctx.lr==0x8051963cu){",
     "if(v114_owner&&post113_flush==1u&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){"),
    ("""    ++post114_syscall;post90_target=ctx.pc;observed_stop_pc=ctx.pc;
    ++post_stops;ctx.is_running=false;
    throw ExceptionStop{}; // stop before authentic syscall vector, never synthesize completion""",
     """    ++post114_syscall;
    check(!post115_vector_active&&post115_vector==0u,
          "V115 async cache syscall vector was already active");
    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;
    const auto gp=ctx.gpr;
    post115_vector_active=true;
    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),
                         [](auto& c){func_80000C00(c);});
    post115_vector_active=false;
    check(post115_vector==1u&&ctx.msr==msr&&ctx.lr==lr&&
          ctx.hid0==hid&&ctx.ctr==ctr,
          "V115 original SC vector did not restore CPU state");
    for(unsigned reg=0;reg<32u;++reg)
      if(reg!=9u&&reg!=10u)
        check(ctx.gpr[reg]==gp[reg],
              "V115 cache syscall clobbered an unrelated guest GPR");
    ++post115_sc;return true; // continue original IOS transport after native rfi"""),
    ("""void trace_call(uint32_t addr, CPUContext&ctx){
   v104_last_hook=addr;v104_last_lr=ctx.lr;""",
     """void trace_call(uint32_t addr, CPUContext&ctx){
   v104_last_hook=addr;v104_last_lr=ctx.lr;
   if(post115_vector_active&&addr==SYSCALL_DEST){
     const bool entry=post114_syscall==1u&&post115_vector==0u&&
          post115_sc==0u&&ctx.lr==0x8051963cu&&
          ctx.pc==SYSCALL_DEST&&ctx.srr0==0x805222ecu&&!(ctx.msr&0x8000u);
     std::cout<<"V115_VECTOR_ENTRY valid="<<entry<<std::endl;
     check(entry,"V115 original SC request syscall vector entry differs");
     ++post115_vector;return;
   }
   if(post115_sc==1u&&addr==POST_OWNER&&ctx.lr==0x80519640u){
     using I=undercover::wii::StmIos;
     const bool route=post115_disable==0u&&post115_vector==1u&&
          post114_syscall==1u&&post113_flush==1u&&post112_submit==1u;
     const bool abi=bool(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD;
     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().event_pending()&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
     std::cout<<"V115_DISABLE_ENTRY route="<<route<<" abi="<<abi
              <<" prior="<<prior<<std::endl;
     check(route&&abi&&prior,"V115 original IOS submission IRQ-disable call differs");
     ++post115_disable;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;
     throw ExceptionStop{}; // stop before executing original IRQ-disable function
   }"""),
    ("nwii::runtime::post114_before=0;",
     "nwii::runtime::post114_before=0;\n     nwii::runtime::post115_vector=nwii::runtime::post115_sc=nwii::runtime::post115_disable=0;\n     nwii::runtime::post115_vector_active=false;"),
    ("check(nwii::runtime::post114_syscall==1u&&",
     "check(nwii::runtime::post115_disable==1u&&nwii::runtime::post115_sc==1u&&nwii::runtime::post115_vector==1u&&nwii::runtime::post114_syscall==1u&&"),
    ("V114_TRIAL_PASS trial=", "V115_TRIAL_PASS trial="),
    ("V114 recovered continuous original __start->SC IOS request flush syscall entry assertions",
     "V115 recovered continuous original __start->SC IOS request cache syscall return and IRQ-disable entry assertions"),
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V115 source anchor missing or ambiguous: "+old[:90]+" count="+str(count))
        s=s.replace(old,new,1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
