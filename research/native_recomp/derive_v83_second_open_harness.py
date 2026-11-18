#!/usr/bin/env python3
"""V83: original first synchronous IOS_Open return to second STM open."""
import argparse
from pathlib import Path
from derive_v82_thread_resume_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x805265d4u",
    "POST_OWNER=0x80519944u"
  ],
  [
    " static uint32_t resume82_sleep_frame=0;",
    " static uint32_t resume82_sleep_frame=0;\n static unsigned open83_restore=0,open83_free=0,open83_free_disable=0,open83_free_restore=0,open83_second=0;"
  ],
  [
    "           if(addr==POST_OWNER&&ctx.lr==0x8052a504u){",
    "           if(addr==INT_RESTORE&&ctx.lr==0x8052a504u){"
  ],
  [
    "             ++resume82_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before restoring nested interrupt state",
    "             ++resume82_stop;return true; // execute original nested interrupt restore"
  ],
  [
    "   if(!submit72_active)return false;\n   if(addr==0x805293b0u){",
    "   if(!submit72_active)return false;\n   if(resume82_stop==1u){\n     using I=undercover::wii::StmIos;\n     if(addr==INT_RESTORE&&ctx.lr==0x805197e0u){\n       check(open83_restore==0u&&ctx.gpr[3]!=0u&&!(ctx.msr&0x8000u)&&\n             ctx.mmu.read32(0x800000e4u)==THREAD,\n             \"V83 original synchronous submit interrupt restore differs\");\n       ++open83_restore;return true;\n     }\n     if(addr==0x8051ad3cu&&ctx.lr==0x80519808u){\n       const bool request=(ctx.gpr[4]&0x3fffffffu)==submit72_phys;\n       const bool result=ipc70_ram.read32(submit72_phys)==I::Reply&&\n           ipc70_ram.read32(submit72_phys+4u)==0u&&ipc70_ram.read32(submit72_phys+8u)==I::Open;\n       const bool route=open83_restore==1u&&open83_free==0u&&(ctx.msr&0x8000u)&&\n           !ipc70_bus.external_irq_level()&&ctx.mmu.read32(0x800000e4u)==THREAD;\n       std::cout<<\"V83_FREE_ENTRY request=\"<<request<<\" result=\"<<result<<\" route=\"<<route<<std::endl;\n       check(request&&result&&route,\"V83 original synchronous submit did not release completed request\");\n       ++open83_free;return true;\n     }\n     if(addr==INT_DISABLE&&ctx.lr==0x8051ad64u){\n       check(open83_free==1u&&open83_free_disable==0u&&(ctx.msr&0x8000u),\n             \"V83 original request free nested interrupt disable differs\");\n       ++open83_free_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051af08u){\n       check(open83_free_disable==1u&&open83_free_restore==0u&&\n             ctx.gpr[3]!=0u&&!(ctx.msr&0x8000u),\n             \"V83 original request free nested interrupt restore differs\");\n       ++open83_free_restore;return true;\n     }\n     if(addr==POST_OWNER&&ctx.lr==0x8052b0b8u){\n       // The next path is checked against the authenticated initialized\n       // source sections without seeding or changing guest memory.\n       std::string next;\n       const uint32_t ptr=ctx.gpr[3];\n       for(const auto& sec:stm70_owner->sections){\n         if(sec.is_bss||sec.is_text||ptr<sec.address||\n            uint64_t(ptr)>=uint64_t(sec.address)+sec.data.size())continue;\n         for(unsigned i=0;i<64u&&uint64_t(ptr-sec.address)+i<sec.data.size();++i){\n           const auto ch=sec.data[ptr-sec.address+i];if(!ch)break;\n           next.push_back(char(ch));\n         }\n         break;\n       }\n       const bool first_device=ipc70_bus.services().is_open(0u,I::Device::Immediate)||\n                              ipc70_bus.services().is_open(0u,I::Device::Event);\n       const bool next_device=(next==\"/dev/stm/eventhook\"&&ipc70_bus.services().is_open(0u,I::Device::Immediate))||\n                              (next==\"/dev/stm/immediate\"&&ipc70_bus.services().is_open(0u,I::Device::Event));\n       const bool abi=ctx.gpr[4]==0u&&ptr!=stm70_path&&ctx.gpr[1]==open71_stack&&\n                      ctx.msr==ipc69_msr&&ctx.mmu.read32(0x800000e4u)==THREAD;\n       const bool cleanup=open83_restore==1u&&open83_free==1u&&open83_free_disable==1u&&\n                          open83_free_restore==1u&&open83_second==0u&&!ipc70_bus.external_irq_level();\n       std::cout<<\"V83_SECOND_OPEN first=\"<<first_device<<\" next=\"<<next_device\n                <<\" abi=\"<<abi<<\" cleanup=\"<<cleanup<<std::endl;\n       check(first_device&&next_device&&abi&&cleanup,\"V83 first original IOS_Open did not return to next STM open\");\n       ++open83_second;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before executing the second original IOS_Open\n     }\n     check(false,\"V83 unexpected original synchronous submit continuation dependency\");\n   }\n   if(addr==0x805293b0u){"
  ],
  [
    "     nwii::runtime::resume82_sleep_frame=0;",
    "     nwii::runtime::resume82_sleep_frame=0;\n     nwii::runtime::open83_restore=nwii::runtime::open83_free=nwii::runtime::open83_free_disable=0;\n     nwii::runtime::open83_free_restore=nwii::runtime::open83_second=0;"
  ],
  [
    "       check(nwii::runtime::resume82_wake_return==1u&&nwii::runtime::resume82_enable==1u&&",
    "       check(nwii::runtime::open83_second==1u&&nwii::runtime::open83_free_restore==1u&&\n             nwii::runtime::resume82_wake_return==1u&&nwii::runtime::resume82_enable==1u&&"
  ],
  [
    "V82_TRIAL_PASS trial=",
    "V83_TRIAL_PASS trial="
  ],
  [
    "V82 recovered continuous original __start->sleeping thread resumed assertions",
    "V83 recovered continuous original __start->second STM open assertions"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x", encoding="utf-8") as f:
        f.write(result)

if __name__ == "__main__":
    main()
