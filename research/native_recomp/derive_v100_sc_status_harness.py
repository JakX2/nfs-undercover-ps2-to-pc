#!/usr/bin/env python3
"""V100 original status getter and data-driven branch."""
import argparse
from pathlib import Path
from derive_v99_post_nand_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051dff4u",
    "POST_OWNER=0x8051dd50u"
  ],
  [
    " static uint32_t post99_dst=0;",
    " static uint32_t post99_dst=0;\n static unsigned post100_entry=0,post100_status=0,post100_route=0;\n static uint32_t post100_choice=0,post100_status_value=0;"
  ],
  [
    "       ++post99_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};",
    "       ++post99_return;return true; // execute original SC status entry"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post99_return==1u){\n       if(addr==0x8051dff4u&&ctx.lr==0x8052fa44u){\n         const bool valid=post100_entry==0u&&ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n              ctx.mmu.read32(R13-3584u)==2u&&post99_verified==3u;\n         std::cout<<\"V100_SC_ENTRY status=\"<<valid<<std::endl;\n         check(valid,\"V100 original SC status helper entry ABI differs\");\n         ++post100_entry;return true;\n       }\n       if(addr==0x8051e5a4u&&ctx.lr==0x8051e020u){\n         const bool valid=post100_entry==1u&&post100_status==0u&&ctx.msr==ipc69_msr&&\n             ctx.mmu.read32(R13-3584u)==2u;\n         std::cout<<\"V100_SC_STATUS entry=\"<<valid<<std::endl;\n         check(valid,\"V100 original SC status getter differs\");\n         ++post100_status;return true;\n       }\n       if((addr==0x8051dd50u&&ctx.lr==0x8051e050u)||\n          (addr==0x8051e5bcu&&ctx.lr==0x8051e054u)){\n         using I=undercover::wii::StmIos;\n         const bool route=post100_entry==1u&&post100_status==1u&&post100_route==0u&&\n              post99_return==1u&&ctx.msr==ipc69_msr&&ctx.mmu.read32(R13-3584u)==2u;\n         const bool thread=ctx.mmu.read16(THREAD+712u)==2u&&\n              ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u;\n         post100_choice=addr==0x8051dd50u?1u:2u;post100_status_value=ctx.gpr[3];\n         std::cout<<\"V100_SC_ROUTE route=\"<<route<<\" thread=\"<<thread<<\" prior=\"<<prior\n                  <<\" chosen=\"<<post100_choice<<std::endl;\n         check(route&&thread&&prior,\"V100 original status-based SC route differs\");\n         ++post100_route;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // genuine branch, neither target is fabricated\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post99_expected.clear();",
    "     nwii::runtime::post99_expected.clear();\n     nwii::runtime::post100_entry=nwii::runtime::post100_status=nwii::runtime::post100_route=0;\n     nwii::runtime::post100_choice=nwii::runtime::post100_status_value=0;"
  ],
  [
    "       check(nwii::runtime::post99_return==1u&&",
    "       check(nwii::runtime::post100_route==1u&&nwii::runtime::post99_return==1u&&"
  ],
  [
    "V99_TRIAL_PASS trial=",
    "V100_TRIAL_PASS trial="
  ],
  [
    "V99 recovered continuous original __start->post NAND memory helper assertions",
    "V100 recovered continuous original __start->SC status routing assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V100 source anchor missing or ambiguous: "+old[:80])
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
