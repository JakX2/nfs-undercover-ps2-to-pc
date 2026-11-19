#!/usr/bin/env python3
"""V113 execute original IOS async submit into native request queue initializer."""
import argparse
from pathlib import Path
from derive_v112_sc_async_submit_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x805195ecu",
    "POST_OWNER=0x805293b0u"
  ],
  [
    " static uint64_t post112_flush_before=0;",
    " static uint64_t post112_flush_before=0;\n static unsigned post113_queue=0;"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x80519924u){",
    "       if(addr==0x805195ecu&&ctx.lr==0x80519924u){"
  ],
  [
    "         ++post112_submit;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // stop before native IPC submission and callback",
    "         ++post112_submit;return true; // execute original IOS transport submission"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post112_submit==1u&&addr==POST_OWNER&&ctx.lr==0x80519630u){\n       using I=undercover::wii::StmIos;\n       const bool route=post113_queue==0u&&post112_submit==1u&&post112_save==1u&&\n           post112_alloc==1u&&post112_disable==1u&&post112_restore==1u&&\n           post112_flush==1u&&post112_sc==1u&&post112_vector==1u;\n       const bool queue=ctx.gpr[3]!=0u&&!(ctx.gpr[3]&3u)&&open71_ram(ctx.gpr[3],8u);\n       const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n           ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n           ctx.mmu.read32(0x800000e4u)==THREAD;\n       const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n           !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n           ipc70_bus.services().event_pending()&&\n           ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n       std::cout<<\"V113_QUEUE_ENTRY route=\"<<route<<\" queue=\"<<queue<<\" abi=\"<<abi<<\" prior=\"<<prior<<std::endl;\n       check(route&&queue&&abi&&prior,\"V113 original IOS transport did not reach queue initializer\");\n       ++post113_queue;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // original queue initializer remains unmodified\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post112_path.clear();",
    "     nwii::runtime::post112_path.clear();nwii::runtime::post113_queue=0;"
  ],
  [
    "check(nwii::runtime::post112_submit==1u&&nwii::runtime::post111_open==1u&&",
    "check(nwii::runtime::post113_queue==1u&&nwii::runtime::post112_submit==1u&&nwii::runtime::post111_open==1u&&"
  ],
  [
    "V112_TRIAL_PASS trial=",
    "V113_TRIAL_PASS trial="
  ],
  [
    "V112 recovered continuous original __start->nonempty SC IOS_OpenAsync request assertions",
    "V113 recovered continuous original __start->SC IOS transport queue entry assertions"
  ]
]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:raise ValueError("V113 source anchor missing or ambiguous: "+old[:90])
        source=source.replace(old,new,1)
    return source
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
