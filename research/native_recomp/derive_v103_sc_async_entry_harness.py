#!/usr/bin/env python3
"""V103 original SC asynchronous wrapper and IOS_OpenAsync entry."""
import argparse
from pathlib import Path
from derive_v102_sc_path_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x804f1e2cu",
    "POST_OWNER=0x8051982cu"
  ],
  [
    " static std::vector<uint8_t> post102_bytes;",
    " static std::vector<uint8_t> post102_bytes;\n static unsigned post103_wrapper=0,post103_save=0,post103_heap=0,post103_alloc=0,post103_alloc_head=0,post103_alloc_disable=0,post103_alloc_restore=0,post103_copy=0,post103_async=0;\n static uint32_t post103_path=0,post103_mode=0,post103_callback=0;"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x8051de3cu){",
    "       if(addr==0x804f1e2cu&&ctx.lr==0x8051de3cu){"
  ],
  [
    "         ++post102_verified;++post102_next;\n         post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};",
    "         ++post102_verified;++post102_next;\n         ++post103_wrapper;return true; // execute the original SC asynchronous file opener"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post102_next==1u&&post103_wrapper==1u){\n       if(addr==0x80545100u&&ctx.lr==0x804f1e40u){\n         const bool fresh=post103_save==0u&&post103_heap==0u;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&\n              ctx.mmu.read16(THREAD+712u)==2u;\n         const bool ok=fresh&&abi;\n         std::cout<<\"V103_SC_SAVE route=\"<<ok<<\" fresh=\"<<fresh<<\" abi=\"<<abi<<std::endl;\n         check(ok,\"V103 original asynchronous wrapper GPR-save ABI differs\");\n         ++post103_save;return true;\n       }\n       if(addr==0x80519094u&&ctx.lr==0x804f1e60u){\n         check(post103_save==1u&&post103_heap==0u&&ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack,\n               \"V103 original async wrapper heap getter differs\");\n         ++post103_heap;return true;\n       }\n       if(addr==0x8051ad38u&&ctx.lr==0x804f1e84u){\n         check(post103_heap==1u&&post103_alloc_head==0u&&post103_alloc==0u,\n               \"V103 original SC allocator wrapper called out of order\");\n         ++post103_alloc_head;return true;\n       }\n       if(addr==0x8051ab34u&&ctx.lr==0x804f1e84u){\n         check(post103_heap==1u&&post103_alloc==0u&&ctx.gpr[4]>=32u&&\n               ctx.gpr[4]<=0x1000u&&ctx.msr==ipc69_msr,\n               \"V103 original SC allocator tail arguments differ\");\n         ++post103_alloc;return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post103_alloc==1u){\n         check(post103_alloc_disable==0u&&(ctx.msr&0x8000u),\n               \"V103 original SC allocator IRQ-disable ABI differs\");\n         ++post103_alloc_disable;return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post103_alloc==1u){\n         check(post103_alloc_disable==1u&&post103_alloc_restore==0u&&!(ctx.msr&0x8000u),\n               \"V103 original SC allocator IRQ-restore ABI differs\");\n         ++post103_alloc_restore;return true;\n       }\n       if(addr==COPY&&ctx.lr==0x804f1eb4u){\n         const auto d=ctx.gpr[3],s=ctx.gpr[4],n=ctx.gpr[5];\n         bool valid=post103_alloc==1u&&post103_copy==0u&&ctx.msr==ipc69_msr&&\n               n>0u&&n<=256u&&open71_ram(d,n)&&open71_ram(s,n);\n         if(valid&&n==post102_bytes.size())\n           for(unsigned i=0;i<n;++i)valid&=ctx.mmu.read8(s+i)==post102_bytes[i];\n         else valid=false;\n         std::cout<<\"V103_SC_COPY bounded=\"<<(n>0u&&n<=256u)<<\" prior=\"<<valid<<std::endl;\n         check(valid,\"V103 original async wrapper did not copy prepared pathname\");\n         ++post103_copy;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x804f1eccu){\n         using I=undercover::wii::StmIos;\n         const auto ptr=ctx.gpr[3];const auto mode=ctx.gpr[4],callback=ctx.gpr[5];\n         bool path=ptr!=0u&&post103_copy==1u&&post102_bytes.size()>1u&&\n                    post102_bytes.size()<=256u&&open71_ram(ptr,uint32_t(post102_bytes.size()));\n         if(path)for(unsigned i=0;i<post102_bytes.size();++i)\n           path&=ctx.mmu.read8(ptr+i)==post102_bytes[i];\n         const bool cb=callback!=0u&&!(callback&3u);\n         const bool route=post103_async==0u&&post103_wrapper==1u&&post103_heap==1u&&\n               post103_alloc==1u&&post103_copy==1u&&ctx.msr==ipc69_msr;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n               !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n               ipc70_bus.services().event_pending()&&\n               ipc70_bus.services().queued_replies()==0u&&\n               !ipc70_bus.external_irq_level();\n         const bool abi=mode<=3u&&ctx.gpr[1]<post98_root_stack&&\n               ctx.mmu.read16(THREAD+712u)==2u&&\n               ctx.mmu.read32(0x800000d4u)==THREAD&&\n               ctx.mmu.read32(0x800000e4u)==THREAD;\n         std::cout<<\"V103_SC_ASYNC_ENTRY route=\"<<route<<\" path=\"<<path<<\" mode=\"<<(mode<=3u)\n                  <<\" callback=\"<<cb<<\" prior=\"<<prior<<\" abi=\"<<abi<<std::endl;\n         check(route&&path&&cb&&prior&&abi,\"V103 original SC asynchronous open ABI differs\");\n         post103_path=ptr;post103_mode=mode;post103_callback=callback;++post103_async;\n         post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // stop before original IOS_OpenAsync request translation\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post102_bytes.clear();",
    "     nwii::runtime::post102_bytes.clear();\n     nwii::runtime::post103_wrapper=nwii::runtime::post103_save=nwii::runtime::post103_heap=nwii::runtime::post103_alloc=nwii::runtime::post103_copy=nwii::runtime::post103_async=0;\n     nwii::runtime::post103_path=nwii::runtime::post103_mode=nwii::runtime::post103_callback=0;"
  ],
  [
    "       check(nwii::runtime::post102_next==1u&&",
    "       check(nwii::runtime::post103_async==1u&&nwii::runtime::post102_next==1u&&"
  ],
  [
    "V102_TRIAL_PASS trial=",
    "V103_TRIAL_PASS trial="
  ],
  [
    "V102 recovered continuous original __start->SC pathname copy return assertions",
    "V103 recovered continuous original __start->SC asynchronous open entry assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V103 source anchor missing or ambiguous: "+old[:80])
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
