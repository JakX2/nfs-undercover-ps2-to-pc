#!/usr/bin/env python3
"""V101 original SC configuration child entry verified through translated body."""
import argparse
from pathlib import Path
from derive_v100_sc_status_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051dd50u",
    "POST_OWNER=0x8051e71cu"
  ],
  [
    " static uint32_t post100_choice=0,post100_status_value=0;",
    " static uint32_t post100_choice=0,post100_status_value=0;\n static unsigned post101_save=0,post101_child=0;\n static uint32_t post101_target=0;"
  ],
  [
    "         ++post100_route;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // genuine branch, neither target is fabricated",
    "         ++post100_route;return true; // execute original selected SC child body"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post100_route==1u&&post100_choice==1u){\n       if(addr==0x80545104u&&ctx.lr==0x8051dd64u){\n         const bool route=post101_save==0u&&post101_child==0u&&ctx.msr==ipc69_msr&&\n              ctx.mmu.read16(THREAD+712u)==2u&&ctx.gpr[1]<post98_root_stack;\n         std::cout<<\"V101_SC_SAVE route=\"<<route<<std::endl;\n         check(route,\"V101 original SC child GPR-save entry differs\");\n         ++post101_save;return true;\n       }\n       if((addr==0x8051e71cu&&ctx.lr==0x8051ddc8u)||\n          (addr==0x8051e518u&&ctx.lr==0x8051ddd8u)){\n         using I=undercover::wii::StmIos;\n         const bool route=post101_save==1u&&post101_child==0u&&post99_return==1u&&\n              ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack;\n         const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n              ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n              ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n         post101_target=addr;\n         const unsigned kind=addr==0x8051e71cu?1u:2u;\n         std::cout<<\"V101_SC_CHILD route=\"<<route<<\" running=\"<<running<<\" prior=\"<<prior\n                  <<\" kind=\"<<kind<<\" arg=\"<<(ctx.gpr[3]!=0u)<<std::endl;\n         check(route&&running&&prior,\"V101 original SC child did not reach selected path\");\n         ++post101_child;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // before executing original child selected by original conditions\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post100_choice=nwii::runtime::post100_status_value=0;",
    "     nwii::runtime::post100_choice=nwii::runtime::post100_status_value=0;\n     nwii::runtime::post101_save=nwii::runtime::post101_child=nwii::runtime::post101_target=0;"
  ],
  [
    "       check(nwii::runtime::post100_route==1u&&",
    "       check(nwii::runtime::post101_child==1u&&nwii::runtime::post100_route==1u&&"
  ],
  [
    "V100_TRIAL_PASS trial=",
    "V101_TRIAL_PASS trial="
  ],
  [
    "V100 recovered continuous original __start->SC status routing assertions",
    "V101 recovered continuous original __start->SC configuration child entry assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V101 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as f:f.write(result)
if __name__=="__main__":main()
