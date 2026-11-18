#!/usr/bin/env python3
"""V93 original ISFS reservation and heap initialization, next service open."""
import argparse
from pathlib import Path
from derive_v92_filesystem_return_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051908cu",
    "POST_OWNER=0x80519944u"
  ],
  [
    " static unsigned post92_complete=0;",
    " static unsigned post92_complete=0;\n static unsigned post93_heap=0,post93_disable=0,post93_restore=0,post93_child=0,post93_open=0;\n static uint32_t post93_reserved=0,post93_base=0,post93_size=0;\n static std::array<uint8_t,32> post93_before{};"
  ],
  [
    "   if(post92_active&&addr==POST_OWNER&&ctx.lr==0x804f0dc4u){",
    "   if(post92_active&&addr==0x8051908cu&&ctx.lr==0x804f0dc4u){"
  ],
  [
    "     ++post92_complete;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // before original next buffer reservation",
    "     ++post92_complete;post93_reserved=ctx.gpr[3];return true; // actual original buffer-low setter\n   }\n   if(post92_complete==1u){\n     using I=undercover::wii::StmIos;\n     const bool preserved=ipc70_bus.services().event_pending()&&!ipc70_bus.external_irq_level()&&\n         ipc70_bus.services().queued_replies()==0u&&ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n         ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n         ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate)&&\n         ipc70_ram.read32(async87_request)==post92_event_command&&\n         ipc70_ram.read32(async87_request+4u)==post92_event_result&&\n         ipc70_ram.read32(async86_out)==post92_event_output;\n     check(preserved,\"V93 resource initialization disturbed earlier device state\");\n     if(addr==0x8051aa04u&&ctx.lr==0x804f0dd8u){\n       const bool route=post93_heap==0u&&ctx.msr==ipc69_msr&&\n            ctx.mmu.read32(R13-3676u)==post93_reserved;\n       const bool bounds=ctx.gpr[3]>=post91_buffer_lo&&ctx.gpr[4]>=32u&&\n            ctx.gpr[4]<=0x10000u&&!(ctx.gpr[3]&31u)&&!(ctx.gpr[4]&31u)&&\n            uint64_t(ctx.gpr[3])+ctx.gpr[4]<=post93_reserved;\n       std::cout<<\"V93_HEAP_ENTRY route=\"<<route<<\" bounds=\"<<bounds<<std::endl;\n       check(route&&bounds,\"V93 second original resource heap lies outside the new IPC reservation\");\n       post93_base=ctx.gpr[3];post93_size=ctx.gpr[4];\n       for(unsigned i=0;i<post93_before.size();++i)post93_before[i]=ctx.mmu.read8(post93_base+i);\n       ++post93_heap;return true;\n     }\n     if(addr==INT_DISABLE&&ctx.lr==0x8051aa2cu){\n       check(post93_heap==1u&&post93_disable==0u&&ctx.msr==ipc69_msr,\n             \"V93 original second heap interrupt disable differs\");\n       ++post93_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051ab14u){\n       check(post93_disable==1u&&post93_restore==0u&&!(ctx.msr&0x8000u)&&ctx.gpr[3]!=0u,\n             \"V93 original second heap interrupt restore differs\");\n       ++post93_restore;return true;\n     }\n     if(addr==0x804f05e8u&&ctx.lr==0x8051e850u){\n       const bool route=post93_heap==1u&&post93_disable==1u&&post93_restore==1u&&post93_child==0u&&\n            ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack;\n       const uint32_t handle=ctx.mmu.read32(R13-3780u);\n       const bool result=handle<16u&&handle!=ctx.mmu.read32(R13-16660u);\n       bool memory=false;\n       for(unsigned i=0;i<post93_before.size();++i)memory|=ctx.mmu.read8(post93_base+i)!=post93_before[i];\n       const bool state=ctx.mmu.read32(R13-3800u)!=0u&&\n           ctx.mmu.read32(R13-16768u)==2u&&ctx.mmu.read32(R13-3676u)==post93_reserved;\n       std::cout<<\"V93_ISFS_RETURN route=\"<<route<<\" result=\"<<result<<\" memory=\"<<memory\n                <<\" state=\"<<state<<\" preserved=\"<<preserved<<std::endl;\n       check(route&&result&&memory&&state,\"V93 original filesystem initialization did not return with its separate heap\");\n       const uint32_t fdptr=R13-16784u;\n       if(ctx.mmu.read32(fdptr)==0u)\n         check(seed_stm_data(ctx,fdptr,4u),\"V93 missing authenticated initial service descriptor\");\n       check(int32_t(ctx.mmu.read32(fdptr))<0,\"V93 original next service descriptor is not unopened\");\n       ++post93_child;return true;\n     }\n     if(addr==POST_OWNER&&ctx.lr==0x804f0614u){\n       const bool route=post93_child==1u&&post93_open==0u&&ctx.msr==ipc69_msr&&\n            ctx.gpr[1]<post91_child_stack&&ctx.gpr[4]==0u&&open71_ram(ctx.gpr[3],8u);\n       std::string pathname;\n       bool terminated=false;\n       for(unsigned i=0;route&&i<64u;++i){\n         if(!open71_ram(ctx.gpr[3]+i,1u)||!seed_stm_data(ctx,ctx.gpr[3]+i,1u))break;\n         const auto ch=ctx.mmu.read8(ctx.gpr[3]+i);\n         if(!ch){terminated=true;break;}\n         pathname.push_back(char(ch));\n       }\n       const bool service=terminated&&pathname==\"/dev/es\";\n       std::cout<<\"V93_NEXT_OPEN route=\"<<route<<\" service=\"<<service<<\" preserved=\"<<preserved<<std::endl;\n       check(route&&service&&preserved,\"V93 next original resource wrapper did not request /dev/es\");\n       ++post93_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before real ES open, never simulate a successful return\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V93_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     check(false,\"V93 unexpected original resource continuation dependency\");return false;"
  ],
  [
    "     nwii::runtime::post92_active=false;nwii::runtime::post92_complete=0;",
    "     nwii::runtime::post92_active=false;nwii::runtime::post92_complete=0;\n     nwii::runtime::post93_heap=nwii::runtime::post93_disable=nwii::runtime::post93_restore=nwii::runtime::post93_child=nwii::runtime::post93_open=0;\n     nwii::runtime::post93_reserved=nwii::runtime::post93_base=nwii::runtime::post93_size=0;\n     nwii::runtime::post93_before.fill(0u);"
  ],
  [
    "       check(nwii::runtime::post92_complete==1u&&",
    "       check(nwii::runtime::post93_open==1u&&nwii::runtime::post92_complete==1u&&"
  ],
  [
    "V92_TRIAL_PASS trial=",
    "V93_TRIAL_PASS trial="
  ],
  [
    "V92 recovered continuous original __start->filesystem open return assertions",
    "V93 recovered continuous original __start->filesystem init and next service open assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V93 source anchor missing or ambiguous")
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as f:
        f.write(result)

if __name__=="__main__":
    main()
