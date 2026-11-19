#!/usr/bin/env python3
"""V111 execute the original nonempty SC async-open wrapper to IOS_OpenAsync."""
import argparse
from pathlib import Path
from derive_v110_sc_strlen_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051e518u",
    "POST_OWNER=0x8051982cu"
  ],
  [
    " static uint32_t post110_source=0,post110_length=0,post110_chosen=0;",
    " static uint32_t post110_source=0,post110_length=0,post110_chosen=0;\n static unsigned post111_wrapper=0,post111_save=0,post111_heap=0,post111_alloc_head=0,post111_alloc=0,post111_disable=0,post111_restore=0,post111_copy=0,post111_open=0;\n static uint32_t post111_copy_dst=0;\n static std::vector<uint8_t> post111_copy_expected;"
  ],
  [
    "       ++post110_next;post90_target=addr;observed_stop_pc=ctx.pc;\n       ++post_stops;ctx.is_running=false;throw ExceptionStop{};",
    "       check(post110_chosen==2u&&post111_wrapper==0u,\n             \"V111 owner SC continuation did not select asynchronous opener\");\n       ++post110_next;++post111_wrapper;\n       return true; // execute original async wrapper, no stubbed return"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post110_next==1u&&post110_chosen==2u&&post111_wrapper==1u){\n       using I=undercover::wii::StmIos;\n       if(addr==0x80545100u&&ctx.lr==0x804f1e40u){\n         check(post111_save==0u&&ctx.msr==ipc69_msr&&ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u),\n               \"V111 original asynchronous wrapper save ABI differs\");\n         ++post111_save;return true;\n       }\n       if(addr==0x80519094u&&ctx.lr==0x804f1e60u){\n         check(post111_save==1u&&post111_heap==0u&&ctx.msr==ipc69_msr,\n               \"V111 original SC heap getter ABI differs\");\n         ++post111_heap;return true;\n       }\n       if(addr==0x8051ad38u&&ctx.lr==0x804f1e84u){\n         check(post111_heap==1u&&post111_alloc_head==0u,\n               \"V111 original SC allocation wrapper order differs\");\n         ++post111_alloc_head;return true;\n       }\n       if(addr==0x8051ab34u&&ctx.lr==0x804f1e84u){\n         check(post111_alloc_head==1u&&post111_alloc==0u&&ctx.gpr[4]>=32u&&ctx.gpr[4]<=0x1000u,\n               \"V111 original SC allocator tail arguments differ\");\n         ++post111_alloc;return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post111_alloc==1u){\n         check(post111_disable==0u&&(ctx.msr&0x8000u),\n               \"V111 original SC allocator interrupt disable differs\");\n         ++post111_disable;return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post111_alloc==1u){\n         check(post111_disable==1u&&post111_restore==0u&&!(ctx.msr&0x8000u),\n               \"V111 original SC allocator interrupt restore differs\");\n         ++post111_restore;return true;\n       }\n       if(addr==COPY&&ctx.lr==0x804f1eb4u){\n         const uint32_t d=ctx.gpr[3],s=ctx.gpr[4],n=ctx.gpr[5];\n         const bool bounded=post111_restore==1u&&post111_copy==0u&&n>0u&&n<=256u&&\n               open71_ram(d,n)&&open71_ram(s,n)&&ctx.msr==ipc69_msr;\n         check(bounded,\"V111 original SC pathname copy range differs\");\n         post111_copy_expected.resize(n);\n         for(unsigned i=0;i<n;++i)post111_copy_expected[i]=ctx.mmu.read8(s+i);\n         post111_copy_dst=d;++post111_copy;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x804f1eccu){\n         const uint32_t ptr=ctx.gpr[3],mode=ctx.gpr[4],cb=ctx.gpr[5];\n         bool copied=post111_copy==1u&&post111_copy_dst!=0u&&!post111_copy_expected.empty()&&\n              open71_ram(post111_copy_dst,uint32_t(post111_copy_expected.size()));\n         if(copied)for(unsigned i=0;i<post111_copy_expected.size();++i)\n             copied&=ctx.mmu.read8(post111_copy_dst+i)==post111_copy_expected[i];\n         bool path=ptr!=0u&&open71_ram(ptr,1u);\n         unsigned n=0u;\n         if(path)for(;n<256u;++n){\n           if(!open71_ram(ptr+n,1u)){path=false;break;}\n           if(ctx.mmu.read8(ptr+n)==0u)break;\n         }\n         path&=n<256u;\n         const bool route=post111_open==0u&&post111_save==1u&&post111_heap==1u&&\n               post111_alloc_head==1u&&post111_alloc==1u&&post111_disable==1u&&post111_restore==1u;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n               mode<=3u&&cb!=0u&&!(cb&3u)&&ctx.mmu.read16(THREAD+712u)==2u&&\n               ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n               !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n               ipc70_bus.services().event_pending()&&\n               ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n         std::cout<<\"V111_SC_ASYNC_ENTRY route=\"<<route<<\" copied=\"<<copied\n                  <<\" path=\"<<path<<\" nonempty=\"<<(n>0u)<<\" abi=\"<<abi<<\" prior=\"<<prior<<std::endl;\n         check(route&&copied&&path&&abi&&prior,\n               \"V111 original nonempty SC async wrapper did not reach IOS_OpenAsync\");\n         ++post111_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // observe, do not dispatch async IOS request yet\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post110_source=nwii::runtime::post110_length=nwii::runtime::post110_chosen=0;",
    "     nwii::runtime::post110_source=nwii::runtime::post110_length=nwii::runtime::post110_chosen=0;\n     nwii::runtime::post111_wrapper=nwii::runtime::post111_save=nwii::runtime::post111_heap=nwii::runtime::post111_alloc_head=nwii::runtime::post111_alloc=nwii::runtime::post111_disable=nwii::runtime::post111_restore=nwii::runtime::post111_copy=nwii::runtime::post111_open=nwii::runtime::post111_copy_dst=0;\n     nwii::runtime::post111_copy_expected.clear();"
  ],
  [
    "check(nwii::runtime::post110_next==1u&&nwii::runtime::post110_strlen==1u&&",
    "check(nwii::runtime::post111_open==1u&&nwii::runtime::post110_next==1u&&nwii::runtime::post110_strlen==1u&&"
  ],
  [
    "V110_TRIAL_PASS trial=",
    "V111_TRIAL_PASS trial="
  ],
  [
    "V110 recovered continuous original __start->nonempty SC strlen continuation assertions",
    "V111 recovered continuous original __start->nonempty SC IOS_OpenAsync entry assertions"
  ],
  [
    "nwii::runtime::post90_route==1u&&nwii::runtime::post90_target==(nwii::runtime::post110_chosen==1u?0x8051e518u:nwii::runtime::post110_chosen==2u?0x804f1e2cu:0x8051e3dcu)&&",
    "nwii::runtime::post90_route==1u&&nwii::runtime::post90_target==POST_OWNER&&"
  ],
  [
    "check(nwii::runtime::post111_open==1u&&",
    "std::cout<<\"V111_TERMINAL open=\"<<nwii::runtime::post111_open\n                 <<\" selected=\"<<nwii::runtime::post110_chosen\n                 <<\" stop=\"<<(nwii::runtime::post90_target==POST_OWNER)<<std::endl;\n       check(nwii::runtime::post111_open==1u&&"
  ]
]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V111 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    return source
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
