#!/usr/bin/env python3
"""V91 original resource initialization through next IOS_Open."""
import argparse
from pathlib import Path
from derive_v90_console_route_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8052f94cu",
    "POST_OWNER=0x80519944u"
  ],
  [
    " static uint32_t post90_target=0;",
    " static uint32_t post90_target=0;\n static unsigned post91_disable=0,post91_restore=0,post91_child=0,post91_lo=0,post91_hi=0,\n                 post91_leaf=0,post91_open=0;\n static uint32_t post91_child_stack=0,post91_buffer_lo=0,post91_buffer_hi=0;"
  ],
  [
    "   if(addr==0x8051e7e4u||addr==POST_OWNER){",
    "   if(addr==0x8051e7e4u||addr==0x8052f94cu){"
  ],
  [
    "     observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // genuine next original child, not a completed stub",
    "     check(first,\"V91 original subsystem selected unimplemented alternate path\");\n     return true; // execute the original next subsystem\n   }\n   if(post90_route==1u&&post90_target==0x8051e7e4u){\n     if(addr==INT_DISABLE&&ctx.lr==0x8051e804u){\n       check(post91_disable==0u&&ctx.msr==ipc69_msr&&ctx.mmu.read32(R13-3584u)==0u,\n             \"V91 new subsystem initial state differs\");\n       ++post91_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051e83cu){\n       check(post91_disable==1u&&post91_restore==0u&&ctx.gpr[3]!=0u&&!(ctx.msr&0x8000u)&&\n             ctx.mmu.read32(R13-3584u)!=0u,\"V91 original subsystem state not committed before interrupt restore\");\n       ++post91_restore;return true;\n     }\n     if(addr==0x804f0cdcu){\n       check(post91_restore==1u&&post91_child==0u&&ctx.lr==0x8051e840u&&ctx.msr==ipc69_msr&&\n             ctx.mmu.read32(R13-3800u)==0u,\"V91 original IOS resource initializer state differs\");\n       post91_child_stack=ctx.gpr[1];++post91_child;return true;\n     }\n     if(addr==0x80519084u&&ctx.lr==0x804f0d04u){\n       check(post91_child==1u&&post91_lo==0u&&ctx.gpr[1]<post91_child_stack,\n             \"V91 original resource buffer-low getter differs\");\n       post91_buffer_lo=ctx.mmu.read32(R13-3676u);\n       check(post91_buffer_lo==ipc69_lo+ipc69_size,\"V91 resource initializer did not inherit IPC reservation\");\n       ++post91_lo;return true;\n     }\n     if(addr==0x8051907cu&&ctx.lr==0x804f0d0cu){\n       check(post91_lo==1u&&post91_hi==0u&&ctx.gpr[3]==post91_buffer_lo&&\n             ctx.mmu.read32(R13-3788u)==post91_buffer_lo,\"V91 original getter return or low bound store differs\");\n       post91_buffer_hi=ctx.mmu.read32(R13-3672u);\n       check(post91_buffer_hi>post91_buffer_lo&&open71_ram(post91_buffer_lo,post91_buffer_hi-post91_buffer_lo),\n             \"V91 original resource IPC bounds invalid\");\n       ++post91_hi;return true;\n     }\n     if(addr==0x8054b4b4u&&ctx.lr==0x804f0d5cu){\n       const bool route=post91_hi==1u&&post91_leaf==0u&&ctx.msr==ipc69_msr;\n       const bool bounds=ctx.mmu.read32(R13-3788u)==post91_buffer_lo&&\n                         ctx.mmu.read32(R13-3784u)==post91_buffer_hi;\n       std::cout<<\"V91_RESOURCE_BUFFER route=\"<<route<<\" bounds=\"<<bounds<<std::endl;\n       check(route&&bounds,\"V91 original IOS buffer preparation differs\");\n       ++post91_leaf;return true;\n     }\n     if(addr==POST_OWNER&&ctx.lr==0x804f0d68u){\n       const bool route=post91_child==1u&&post91_lo==1u&&post91_hi==1u&&post91_leaf==1u&&post91_open==0u;\n       const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post91_child_stack&&ctx.gpr[2]==ipc69_gprs[2]&&\n                      ctx.gpr[13]==ipc69_gprs[13]&&ctx.gpr[4]<=3u&&open71_ram(ctx.gpr[3],1u);\n       std::string path;\n       if(abi)for(unsigned i=0;i<64u;++i){\n         if(!open71_ram(ctx.gpr[3]+i,1u))break;\n         // Original literal path may be omitted from the reduced fixture.\n         // Only copy authenticated data at the true pointer, never change\n         // the guest's path register or fabricate a request / return.\n         if(i==0u)(void)seed_stm_data(ctx,ctx.gpr[3],1u);\n         else (void)seed_stm_data(ctx,ctx.gpr[3]+i,1u);\n         const auto ch=ctx.mmu.read8(ctx.gpr[3]+i);\n         if(!ch)break;\n         path.push_back(char(ch));\n       }\n       const unsigned device=path==\"/dev/fs\"?1u:path==\"/dev/es\"?2u:path==\"/dev/di\"?3u:\n                             path==\"/dev/flash\"?4u:0u;\n       const bool valid=device!=0u;\n       const bool devices=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n                          ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n       std::cout<<\"V91_RESOURCE_OPEN route=\"<<route<<\" abi=\"<<abi<<\" path=\"<<valid\n                <<\" devices=\"<<devices<<\" pending=\"<<pending<<\" kind=\"<<device<<std::endl;\n       check(route&&abi&&valid&&devices&&pending,\"V91 original IOS resource open did not reach authenticated path\");\n       ++post91_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original next IOS_Open\n     }"
  ],
  [
    "     nwii::runtime::post90_mem2=nwii::runtime::post90_route=0;nwii::runtime::post90_target=0;",
    "     nwii::runtime::post90_mem2=nwii::runtime::post90_route=0;nwii::runtime::post90_target=0;\n     nwii::runtime::post91_disable=nwii::runtime::post91_restore=nwii::runtime::post91_child=0;\n     nwii::runtime::post91_lo=nwii::runtime::post91_hi=nwii::runtime::post91_leaf=nwii::runtime::post91_open=0;\n     nwii::runtime::post91_child_stack=nwii::runtime::post91_buffer_lo=nwii::runtime::post91_buffer_hi=0;"
  ],
  [
    "       check(nwii::runtime::post90_route==1u&&(nwii::runtime::post90_target==0x8051e7e4u||nwii::runtime::post90_target==POST_OWNER)&&",
    "       check(nwii::runtime::post91_open==1u&&nwii::runtime::post90_route==1u&&nwii::runtime::post90_target==POST_OWNER&&"
  ],
  [
    "V90_TRIAL_PASS trial=",
    "V91_TRIAL_PASS trial="
  ],
  [
    "V90 recovered continuous original __start->post STM original dependency assertions",
    "V91 recovered continuous original __start->next IOS resource open assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V91 source anchor missing or ambiguous")
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
