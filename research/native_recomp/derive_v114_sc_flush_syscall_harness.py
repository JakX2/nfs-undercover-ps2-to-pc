#!/usr/bin/env python3
"""V114 execute original IOS request DCFlushRange to its authentic syscall boundary."""
import argparse
from pathlib import Path
from derive_v113_sc_transport_queue_harness import derive as previous

EDITS = [
    ("POST_OWNER=0x805222c0u", "POST_OWNER=0x805222e8u"),
    (" static unsigned post113_flush=0;",
     " static unsigned post113_flush=0;\n static unsigned post114_syscall=0;\n static uint32_t post114_base=0,post114_len=0;\n static uint64_t post114_before=0;"),
    ("if(post112_submit==1u&&addr==POST_OWNER&&ctx.lr==0x8051963cu){",
     "if(post112_submit==1u&&addr==0x805222c0u&&ctx.lr==0x8051963cu){"),
    ("       ++post113_flush;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // original cache flush remains unmodified",
     "       post114_base=ctx.gpr[3];post114_len=ctx.gpr[4];\n       post114_before=ctx.guest_flush_count;\n       ++post113_flush;return true; // execute genuine original cache flush body"),
    ("bool handle_syscall(CPUContext&ctx){",
     """bool handle_syscall(CPUContext&ctx){
  const bool v114_owner=ctx.mmu.read32(0x80000048u)==0x004e5090u;
  if(v114_owner&&post113_flush==1u&&ctx.pc==POST_OWNER&&ctx.lr==0x8051963cu){
    using I=undercover::wii::StmIos;
    const uint64_t lines=((post114_base&31u)+uint64_t(post114_len)+31u)/32u;
    const bool route=post114_syscall==0u&&post112_submit==1u&&
          post112_save==1u&&post112_alloc==1u&&post112_flush==1u&&
          post112_sc==1u&&post112_vector==1u;
    const bool flushed=post114_len>=32u&&post114_len<=0x1000u&&
          open71_ram(post114_base,post114_len)&&
          ctx.guest_flush_count==post114_before+lines;
    const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u;
    const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().event_pending()&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
    std::cout<<"V114_CACHE_SYSCALL route="<<route<<" flushed="<<flushed
             <<" abi="<<abi<<" prior="<<prior<<std::endl;
    check(route&&flushed&&abi&&prior,"V114 original IOS request flush syscall ABI differs");
    ++post114_syscall;post90_target=ctx.pc;observed_stop_pc=ctx.pc;
    ++post_stops;ctx.is_running=false;
    throw ExceptionStop{}; // stop before authentic syscall vector, never synthesize completion
  }"""),
    ("nwii::runtime::post113_flush=0;",
     "nwii::runtime::post113_flush=0;\n     nwii::runtime::post114_syscall=0;\n     nwii::runtime::post114_base=nwii::runtime::post114_len=0;\n     nwii::runtime::post114_before=0;"),
    ("check(nwii::runtime::post113_flush==1u&&",
     "check(nwii::runtime::post114_syscall==1u&&nwii::runtime::post113_flush==1u&&"),
    ("V113_TRIAL_PASS trial=", "V114_TRIAL_PASS trial="),
    ("V113 recovered continuous original __start->SC IOS transport flush entry assertions",
     "V114 recovered continuous original __start->SC IOS request flush syscall entry assertions"),
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V114 source anchor missing or ambiguous: "+old[:100]+" count="+str(count))
        s=s.replace(old,new,1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
