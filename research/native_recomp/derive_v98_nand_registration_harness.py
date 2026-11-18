#!/usr/bin/env python3
"""V98 actual original NAND shutdown list insertion and registration tail."""
import argparse
from pathlib import Path
from derive_v97_es_close_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x80527b4cu",
    "POST_OWNER=0x8051e5bcu"
  ],
  [
    " static uint32_t post97_dst=0;",
    " static uint32_t post97_dst=0;\n static uint32_t post98_node=0,post98_callback=0,post98_priority=0,post98_version_ptr=0;\n static unsigned post98_disable=0,post98_restore=0,post98_version=0,post98_report=0,post98_return=0;"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool post98_list(CPUContext&ctx){\n   const std::array<uint32_t,3> nodes{{SHUTDOWN_NODE,MI_NODE,post98_node}};\n   std::array<bool,3> seen{};\n   uint32_t node=ctx.mmu.read32(SHUTDOWN_HEAD),prev=0,priority=0;\n   for(unsigned i=0;i<nodes.size();++i){\n     const auto it=std::find(nodes.begin(),nodes.end(),node);\n     if(node==0u||it==nodes.end())return false;\n     const auto index=unsigned(it-nodes.begin());\n     if(seen[index]||ctx.mmu.read32(node+12u)!=prev)return false;\n     seen[index]=true;\n     const auto cur=ctx.mmu.read32(node+4u);\n     if(i&&cur<priority)return false;\n     priority=cur;prev=node;node=ctx.mmu.read32(node+8u);\n   }\n   return node==0u&&ctx.mmu.read32(SHUTDOWN_TAIL)==prev&&\n      ctx.mmu.read32(post98_node)==post98_callback&&ctx.mmu.read32(post98_node+4u)==post98_priority;\n }\n static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post97_return==1u&&post98_node){\n     using I=undercover::wii::StmIos;\n     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n          !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n          ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate)&&\n          ipc70_bus.services().event_pending()&&ipc70_ram.read32(async87_request)==post92_event_command&&\n          ipc70_ram.read32(async87_request+4u)==post92_event_result&&ipc70_ram.read32(async86_out)==post92_event_output&&\n          !ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u;\n     check(prior&&post98_list(ctx),\"V98 NAND registration did not preserve existing callback and IOS state\");\n     if(addr==INT_DISABLE&&(ctx.lr==0x8051e8c4u||ctx.lr==0x8051e8e4u)){\n       const bool first=post98_disable==0u&&post98_restore==0u&&ctx.lr==0x8051e8c4u;\n       const bool second=post98_disable==1u&&post98_restore==1u&&post98_report==1u&&ctx.lr==0x8051e8e4u;\n       check((first||second)&&ctx.msr==ipc69_msr,\"V98 original NAND interrupt disable sequence\");\n       ++post98_disable;return true;\n     }\n     if(addr==INT_RESTORE&&(ctx.lr==0x8051e8d0u||ctx.lr==0x8051e8f0u)){\n       check(post98_disable==post98_restore+1u&&post98_disable<=2u&&!(ctx.msr&0x8000u)&&ctx.gpr[3]!=0u,\n             \"V98 original NAND interrupt restore sequence\");\n       ++post98_restore;return true;\n     }\n     if(addr==0x80521018u&&ctx.lr==0x8051e8d8u){\n       check(post98_restore==1u&&post98_version==0u&&ctx.msr==ipc69_msr,\"V98 original NAND version registration ABI\");\n       post98_version_ptr=ctx.gpr[3];\n       bool valid=false;\n       for(const auto& sec:stm70_owner->sections){\n         if(sec.is_bss||sec.is_text||post98_version_ptr<sec.address||\n            uint64_t(post98_version_ptr)>=uint64_t(sec.address)+sec.data.size())continue;\n         for(unsigned i=0;i<256u&&uint64_t(post98_version_ptr-sec.address)+i<sec.data.size();++i)\n           if(!sec.data[post98_version_ptr-sec.address+i]){valid=i>0u;break;}\n       }\n         std::cout<<\"V98_VERSION_POINTER nonzero=\"<<(post98_version_ptr!=0u)<<\" owner=\"<<valid<<std::endl;\n       check(valid,\"V98 NAND version pointer not owner initialized\");\n       ++post98_version;return true;\n     }\n     if(addr==REPORT&&ctx.lr==0x8051e8d8u){\n       check(post98_version==1u&&ctx.gpr[3]==R13-16436u&&ctx.gpr[4]==post98_version_ptr,\n             \"V98 original NAND version log sink ABI\");\n       return true;\n     }\n     if(addr==POST_OWNER&&ctx.lr==0x8051e8f8u){\n       const bool route=post98_disable==2u&&post98_restore==2u&&post98_return==0u&&post98_report==1u;\n       const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack&&ctx.mmu.read16(THREAD+712u)==2u&&\n             ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n       bool directory=true;\n       for(unsigned i=0;i<POST96_DIRECTORY.size();++i)directory&=ctx.mmu.read8(post97_dst+i)==uint8_t(POST96_DIRECTORY[i]);\n       directory&=ctx.mmu.read8(post97_dst+POST96_DIRECTORY.size())==0u;\n       const bool state=ctx.mmu.read32(R13-3584u)!=0u&&ctx.mmu.read32(R13-16768u)==2u&&ctx.mmu.read32(R13-16784u)==0xffffffffu;\n       std::cout<<\"V98_NAND_CALLBACK route=\"<<route<<\" abi=\"<<abi<<\" list=\"<<post98_list(ctx)\n                <<\" directory=\"<<directory<<\" state=\"<<state<<\" prior=\"<<prior<<std::endl;\n       check(route&&abi&&directory&&state,\"V98 original NAND callback registration did not reach next initializer\");\n       ++post98_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{};\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V98_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     check(false,\"V98 unexpected NAND registration dependency\");\n   }"
  ],
  [
    "   if(post96_phase==4u&&addr==POST_OWNER&&ctx.lr==0x8051e8c0u){",
    "   if(post96_phase==4u&&addr==0x80527b4cu&&ctx.lr==0x8051e8c0u){"
  ],
  [
    "     ++post97_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{};",
    "     post98_node=ctx.gpr[3];\n     check(post98_node!=SHUTDOWN_NODE&&post98_node!=MI_NODE&&\n           ctx.mmu.read32(SHUTDOWN_HEAD)==SHUTDOWN_NODE&&ctx.mmu.read32(SHUTDOWN_TAIL)==MI_NODE&&\n           ctx.mmu.read32(SHUTDOWN_NODE+8u)==MI_NODE&&ctx.mmu.read32(MI_NODE+12u)==SHUTDOWN_NODE,\n           \"V98 previous shutdown list geometry differs before authentic insertion\");\n     // Reduced executable omitted initialized callback data. Load only\n     // the two authenticated initial fields, before original insertion.\n     if(ctx.mmu.read32(post98_node)==0u)\n       check(seed_stm_data(ctx,post98_node,8u),\"V98 original NAND shutdown node initial fields missing\");\n     post98_callback=ctx.mmu.read32(post98_node);post98_priority=ctx.mmu.read32(post98_node+4u);\n     check(post98_callback>=0x80004000u&&post98_callback<0x81800000u&&!(post98_callback&3u)&&\n           original_word(post98_callback)!=0u&&post98_priority<=0x1000u,\n           \"V98 original NAND shutdown callback metadata invalid\");\n     check(ctx.mmu.read32(post98_node+8u)==0u&&ctx.mmu.read32(post98_node+12u)==0u,\n           \"V98 NAND shutdown node already linked\");\n     ++post97_return;return true; // actual original registration"
  ],
  [
    "  if(own&&post89_entry==1u&&ctx.pc==REPORT&&ctx.lr==0x8052f7d0u){",
    "  if(own&&post98_version==1u&&ctx.pc==REPORT&&ctx.lr==0x8051e8d8u){\n    check(post98_report==0u&&ctx.gpr[3]==R13-16436u&&ctx.gpr[4]==post98_version_ptr,\n          \"V98 NAND version report sink differs\");\n    ++post98_report;return true;\n  }\n  if(own&&post89_entry==1u&&ctx.pc==REPORT&&ctx.lr==0x8052f7d0u){"
  ],
  [
    "     nwii::runtime::post97_copy=nwii::runtime::post97_close=nwii::runtime::post97_return=nwii::runtime::post97_dst=0;",
    "     nwii::runtime::post97_copy=nwii::runtime::post97_close=nwii::runtime::post97_return=nwii::runtime::post97_dst=0;\n     nwii::runtime::post98_node=nwii::runtime::post98_callback=nwii::runtime::post98_priority=nwii::runtime::post98_version_ptr=0;\n     nwii::runtime::post98_disable=nwii::runtime::post98_restore=nwii::runtime::post98_version=nwii::runtime::post98_report=nwii::runtime::post98_return=0;"
  ],
  [
    "       check(nwii::runtime::post97_return==1u&&",
    "       check(nwii::runtime::post98_return==1u&&nwii::runtime::post97_return==1u&&"
  ],
  [
    "      check(c.mmu.read32(SHUTDOWN_HEAD)==SHUTDOWN_NODE &&\n            c.mmu.read32(SHUTDOWN_TAIL)==MI_NODE&&\n            c.mmu.read32(MI_NODE+8u)==0u&&c.mmu.read32(MI_NODE+12u)==SHUTDOWN_NODE&&",
    "      check(nwii::runtime::post98_list(c)&&"
  ],
  [
    "      check(c.mmu.read32(SHUTDOWN_NODE+8u)==MI_NODE &&\n            c.mmu.read32(SHUTDOWN_NODE+12u)==0u &&\n            c.mmu.read32(SHUTDOWN_NODE+4u)==100u+trial,",
    "      check(c.mmu.read32(SHUTDOWN_NODE+4u)==100u+trial,"
  ],
  [
    "V97_TRIAL_PASS trial=",
    "V98_TRIAL_PASS trial="
  ],
  [
    "V97 recovered continuous original __start->ES close return assertions",
    "V98 recovered continuous original __start->NAND callback registration assertions"
  ],
  [
    "     check(first,\"V91 original subsystem selected unimplemented alternate path\");\n     return true; // execute the original next subsystem",
    "     check(first,\"V91 original subsystem selected unimplemented alternate path\");\n     // Restore only omitted owner-initialized SDA data that the original\n     // NAND root loads before its own store. The original instructions\n     // still load the pointers and select the actual version argument.\n     unsigned seeded=0;\n     for(uint32_t pc=0x8051e7e4u;pc<0x8051e8f8u;pc+=4u){\n       const auto op=original_word(pc),major=op>>26,ra=(op>>16)&31u;\n       if((ra!=2u&&ra!=13u)||major!=32u)continue;\n       bool written=false;\n       for(uint32_t q=0x8051e7e4u;q<pc;q+=4u){\n         const auto prev=original_word(q),kind=prev>>26;\n         if((kind==36u||kind==38u||kind==44u)&&((prev>>16)&31u)==ra&&\n            (prev&0xffffu)==(op&0xffffu))written=true;\n       }\n       const auto address=ctx.gpr[ra]+uint32_t(int32_t(int16_t(op&0xffffu)));\n       if(!written&&ctx.mmu.read32(address)==0u&&seed_stm_data(ctx,address,4u))++seeded;\n     }\n     std::cout<<\"V98_INITIAL_DATA count=\"<<seeded<<std::endl;\n     return true; // execute the original next subsystem"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V98 source anchor missing or ambiguous: "+old[:80])
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
