#!/usr/bin/env python3
"""V110 execute original nonempty SC strlen and check genuine next call."""
import argparse
from pathlib import Path
from derive_v109_sc_nonempty_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x80544ac0u",
    "POST_OWNER=0x8051e518u"
  ],
  [
    " static std::vector<uint8_t> post109_expected;",
    " static std::vector<uint8_t> post109_expected;\n static unsigned post110_strlen=0,post110_next=0;\n static uint32_t post110_source=0,post110_length=0,post110_chosen=0;"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x8051e7a4u){",
    "       if(addr==0x80544ac0u&&ctx.lr==0x8051e7a4u){"
  ],
  [
    "         ++post109_return;post90_target=addr;observed_stop_pc=ctx.pc;\n         ++post_stops;ctx.is_running=false;throw ExceptionStop{};",
    "         const uint32_t source=ctx.gpr[3];\n         bool valid=source!=0u&&open71_ram(source,1u)&&post110_strlen==0u;\n         unsigned n=0u;\n         if(valid)for(;n<256u;++n){\n           if(!open71_ram(source+n,1u)){valid=false;break;}\n           if(ctx.mmu.read8(source+n)==0u)break;\n         }\n         valid&=n<256u;\n         std::cout<<\"V110_SC_STRLEN input=\"<<valid<<\" bounded=\"<<(n<256u)\n                  <<\" empty=\"<<(n==0u)<<std::endl;\n         check(valid,\"V110 original second SC length input differs\");\n         post110_source=source;post110_length=n;\n         ++post109_return;++post110_strlen;\n         return true; // original PowerPC strlen executes"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post110_strlen==1u&&post110_next==0u&&\n        ((addr==0x8051e518u&&ctx.lr==0x8051ddd8u)||\n         (addr==0x804f1e2cu&&ctx.lr==0x8051de3cu)||\n         (addr==0x8051e3dcu&&ctx.lr==0x8051e78cu))){\n       using I=undercover::wii::StmIos;\n       const bool routed=post109_return==1u&&post109_copy==1u&&post102_strlen==1u;\n       bool data=!post109_expected.empty()&&post109_dst!=0u&&\n                 ctx.mmu.read8(post110_source+post110_length)==0u;\n       if(data)for(unsigned i=0;i<post109_expected.size();++i)\n         data&=ctx.mmu.read8(post109_dst+i)==post109_expected[i];\n       const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n              ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n              ctx.mmu.read32(0x800000e4u)==THREAD;\n       const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n              ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n              !ipc70_bus.external_irq_level();\n       post110_chosen=addr==0x8051e518u?1u:addr==0x804f1e2cu?2u:3u;\n       std::cout<<\"V110_SC_CONTINUE route=\"<<routed<<\" data=\"<<data<<\" abi=\"<<abi\n                <<\" prior=\"<<prior<<\" branch=\"<<post110_chosen<<std::endl;\n       check(routed&&data&&abi&&prior,\"V110 original SC length did not return into authentic child\");\n       std::cout<<\"V110_IPC_GATE ack=\"<<(ack77_reply==1u)\n                <<\" dispatch=\"<<(irq76_ipc==1u)\n                <<\" vector=\"<<(vector75_handler==1u)\n                <<\" scheduler=\"<<(sched74_irq==1u)\n                <<\" active=\"<<ipc69_active\n                <<\" phase=\"<<(ipc69_step==9u)<<std::endl;\n       ++post110_next;post90_target=addr;observed_stop_pc=ctx.pc;\n       ++post_stops;ctx.is_running=false;throw ExceptionStop{};\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post109_expected.clear();",
    "     nwii::runtime::post109_expected.clear();\n     nwii::runtime::post110_strlen=nwii::runtime::post110_next=0;\n     nwii::runtime::post110_source=nwii::runtime::post110_length=nwii::runtime::post110_chosen=0;"
  ],
  [
    "check(nwii::runtime::post109_return==1u&&nwii::runtime::post109_copy==1u&&",
    "check(nwii::runtime::post110_next==1u&&nwii::runtime::post110_strlen==1u&&nwii::runtime::post109_return==1u&&nwii::runtime::post109_copy==1u&&"
  ],
  [
    "V109_TRIAL_PASS trial=",
    "V110_TRIAL_PASS trial="
  ],
  [
    "V109 recovered continuous original __start->nonempty SC second string copy assertions",
    "V110 recovered continuous original __start->nonempty SC strlen continuation assertions"
  ],
  [
    "       if((addr==0x8051e71cu&&ctx.lr==0x8051ddc8u)||\n          (addr==0x8051e518u&&ctx.lr==0x8051ddd8u)){",
    "       if(post101_child==0u&&((addr==0x8051e71cu&&ctx.lr==0x8051ddc8u)||\n          (addr==0x8051e518u&&ctx.lr==0x8051ddd8u))){"
  ],
  [
    "  for(unsigned trial=0;trial<trials;++trial){\n    if(owner&&trial!=0u){",
    "  for(unsigned trial=0;trial<trials;++trial){\n    if(owner)std::cout<<\"V110_TRIAL_START trial=\"<<(trial+1u)<<std::endl;\n    if(owner&&trial!=0u){"
  ],
  [
    "    throw std::runtime_error(why);",
    "    std::cout<<\"V110_ASSERT_HOOK pc=\"<<std::hex<<v104_last_hook<<\" lr=\"<<v104_last_lr<<std::dec<<std::endl;\n    throw std::runtime_error(why);"
  ],
  [
    "       if(addr==0x804f1e2cu&&ctx.lr==0x8051de3cu){",
    "       if(post110_strlen==0u&&addr==0x804f1e2cu&&ctx.lr==0x8051de3cu){"
  ]
]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V110 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    return source
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
