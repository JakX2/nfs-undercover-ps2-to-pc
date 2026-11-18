#!/usr/bin/env python3
"""V89 original post-STM subsystem to console identifier."""
import argparse
from pathlib import Path
from derive_v88_stm_return_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x80520968u",
    "POST_OWNER=0x8051fd44u"
  ],
  [
    " static std::array<uint32_t,32> async88_gprs{};",
    " static std::array<uint32_t,32> async88_gprs{};\n static unsigned post89_entry=0,post89_disable=0,post89_restore=0,post89_version=0,post89_report=0,post89_queue=0,post89_stop=0;\n static uint32_t post89_version_ptr=0,post89_queue_ptr=0;"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool post89_trace(uint32_t addr,CPUContext&ctx){\n   using I=undercover::wii::StmIos;\n   const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n             ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n   const bool pending=ipc70_bus.services().event_pending()&&!ipc70_bus.external_irq_level()&&\n                      ipc70_bus.services().queued_replies()==0u&&ipc70_ram.read32(async87_request)==I::Ioctl;\n   check(running&&pending,\"V89 post-STM startup lost running thread or deferred event\");\n   if(addr==0x8052f790u){\n    using I=undercover::wii::StmIos;using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n    const bool route=async88_rfi==1u&&async88_stop==0u&&ctx.lr==0x8052096cu&&ctx.gpr[1]==ipc69_gprs[1];\n    bool abi=ctx.msr==ipc69_msr&&ctx.gpr[2]==ipc69_gprs[2]&&ctx.gpr[13]==ipc69_gprs[13];\n    for(unsigned r=14;r<32u;++r)abi&=ctx.gpr[r]==ipc69_gprs[r];\n    const bool running=ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n                       ctx.mmu.read32(0x800000e4u)==THREAD;\n    const bool deferred=ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n          ipc70_ram.read32(async87_request)==I::Ioctl&&!ipc70_bus.external_irq_level()&&\n          (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u)&(M::X1|M::Y1|M::Y2))==0u;\n    const bool devices=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n                       ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n    std::cout<<\"V88_STM_RETURN route=\"<<route<<\" abi=\"<<abi<<\" running=\"<<running\n             <<\" deferred=\"<<deferred<<\" devices=\"<<devices<<std::endl;\n    check(route&&abi&&running&&deferred&&devices,\"V88 original STM init did not return to OSInit\");\n    check(post89_entry==0u&&ctx.pc==addr,\"V89 next original OSInit subsystem entered twice\");\n    ++async88_stop;++post89_entry;\n    // Restore only missing, authenticated initialized data for direct SDA\n    // operands read before the subsystem's first version-registration call.\n    // Never overwrite live nonzero runtime values or writes by this body.\n    for(uint32_t pc=addr;pc<0x8052f7d0u;pc+=4u){\n      const auto op=original_word(pc),major=op>>26,ra=(op>>16)&31u;\n      if((ra==2u||ra==13u)&&major==32u){\n        const auto a=ctx.gpr[ra]+uint32_t(int32_t(int16_t(op&0xffffu)));\n        bool written=false;\n        for(uint32_t q=addr;q<pc;q+=4u){\n          const auto prev=original_word(q),kind=prev>>26;\n          if((kind==36u||kind==38u||kind==44u)&&((prev>>16)&31u)==ra&&(prev&0xffffu)==(op&0xffffu))written=true;\n        }\n        if(!written&&ctx.mmu.read32(a)==0u)(void)seed_stm_data(ctx,a,4u);\n      }\n    }\n    return true;\n   }\n   check(post89_entry==1u,\"V89 next subsystem helper before authentic entry\");\n   if(addr==INT_DISABLE&&ctx.lr==0x8052f7a4u){\n     check(post89_disable==0u&&ctx.msr==ipc69_msr&&ctx.gpr[1]<ipc69_gprs[1],\n          \"V89 next subsystem native interrupt disable differs\");\n     ++post89_disable;return true;\n   }\n   if(addr==INT_RESTORE&&(ctx.lr==0x8052f7b4u||ctx.lr==0x8052f7c8u)){\n     check(post89_disable==1u&&post89_restore==0u&&ctx.gpr[3]!=0u&&!(ctx.msr&0x8000u),\n           \"V89 next subsystem interrupt restore differs\");\n     ++post89_restore;return true;\n   }\n   if(addr==0x80521018u){\n     check(post89_restore==1u&&post89_version==0u&&ctx.lr==0x8052f7d0u&&ctx.msr==ipc69_msr,\n           \"V89 original version registration call differs\");\n     post89_version_ptr=ctx.gpr[3];\n     bool text=false;\n     for(const auto& sec:stm70_owner->sections){\n       if(sec.is_bss||sec.is_text||post89_version_ptr<sec.address||\n          uint64_t(post89_version_ptr)>=uint64_t(sec.address)+sec.data.size())continue;\n       for(unsigned i=0;i<256u&&uint64_t(post89_version_ptr-sec.address)+i<sec.data.size();++i){\n         const auto ch=sec.data[post89_version_ptr-sec.address+i];\n         if(!ch){text=i>0u;break;}\n       }\n     }\n     check(text,\"V89 original subsystem version pointer not initialized from owner data\");\n     ++post89_version;return true;\n   }\n   if(addr==REPORT&&ctx.lr==0x8052f7d0u){\n     check(post89_version==1u&&ctx.gpr[3]==R13-16436u&&ctx.gpr[4]==post89_version_ptr,\n           \"V89 original version registration report tail ABI differs\");\n     return true;\n   }\n   if(addr==0x805293b0u){\n     check(post89_version==1u&&post89_report==1u&&post89_queue==0u&&ctx.lr==0x8052f7dcu&&\n           ctx.msr==ipc69_msr&&open71_ram(ctx.gpr[3],8u),\"V89 new original queue initializer ABI differs\");\n     post89_queue_ptr=ctx.gpr[3];++post89_queue;return true;\n   }\n   if(addr==POST_OWNER&&ctx.lr==0x8052f7e0u){\n     const bool route=post89_entry==1u&&post89_disable==1u&&post89_restore==1u&&\n           post89_stop==0u&&async88_stop==1u;\n     const bool queue=post89_queue==1u&&ctx.mmu.read32(post89_queue_ptr)==0u&&\n           ctx.mmu.read32(post89_queue_ptr+4u)==0u;\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<ipc69_gprs[1]&&ctx.gpr[2]==ipc69_gprs[2]&&\n           ctx.gpr[13]==ipc69_gprs[13];\n     const bool version=post89_version==1u&&post89_report==1u;\n     std::cout<<\"V89_SUBSYSTEM route=\"<<route<<\" queue=\"<<queue<<\" abi=\"<<abi\n              <<\" version=\"<<version<<\" pending=\"<<pending<<std::endl;\n     check(route&&queue&&abi&&version&&pending,\"V89 original next subsystem did not reach console query\");\n     ++post89_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // exact original console classification entry\n   }\n   if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n     std::cout<<\"V89_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n   check(false,\"V89 unexpected post-STM native dependency\");return false;\n }\n\n static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(async88_rfi==1u)return post89_trace(addr,ctx);"
  ],
  [
    "bool handle_syscall(CPUContext&ctx){\n  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;\n  if(own&&async87_deferred==1u&&ctx.pc==POST_OWNER){\n    using I=undercover::wii::StmIos;using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n    const bool route=async88_rfi==1u&&async88_stop==0u&&ctx.lr==POST_OWNER&&ctx.gpr[1]==ipc69_gprs[1];\n    bool abi=ctx.msr==ipc69_msr&&ctx.gpr[2]==ipc69_gprs[2]&&ctx.gpr[13]==ipc69_gprs[13];\n    for(unsigned r=14;r<32u;++r)abi&=ctx.gpr[r]==ipc69_gprs[r];\n    const bool running=ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n                       ctx.mmu.read32(0x800000e4u)==THREAD;\n    const bool deferred=ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n          ipc70_ram.read32(async87_request)==I::Ioctl&&!ipc70_bus.external_irq_level()&&\n          (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u)&(M::X1|M::Y1|M::Y2))==0u;\n    const bool devices=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n                       ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n    std::cout<<\"V88_STM_RETURN route=\"<<route<<\" abi=\"<<abi<<\" running=\"<<running\n             <<\" deferred=\"<<deferred<<\" devices=\"<<devices<<std::endl;\n    check(route&&abi&&running&&deferred&&devices,\"V88 original STM init did not return to OSInit\");\n    ++async88_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n    throw ExceptionStop{}; // existing owner-only stop at original OSInit next callsite\n  }",
    "bool handle_syscall(CPUContext&ctx){\n  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;\n  if(own&&post89_entry==1u&&ctx.pc==REPORT&&ctx.lr==0x8052f7d0u){\n    check(post89_version==1u&&post89_report==0u&&ctx.gpr[3]==R13-16436u&&ctx.gpr[4]==post89_version_ptr,\n          \"V89 original registration log sink ABI differs\");\n    ++post89_report;return true; // inherited explicit logging sink only\n  }"
  ],
  [
    "     nwii::runtime::async88_gprs.fill(0u);",
    "     nwii::runtime::async88_gprs.fill(0u);\n     nwii::runtime::post89_entry=nwii::runtime::post89_disable=nwii::runtime::post89_restore=0;\n     nwii::runtime::post89_version=nwii::runtime::post89_report=nwii::runtime::post89_queue=nwii::runtime::post89_stop=0;\n     nwii::runtime::post89_version_ptr=nwii::runtime::post89_queue_ptr=0;"
  ],
  [
    "       check(nwii::runtime::async88_stop==1u&&nwii::runtime::async88_rfi==1u&&",
    "       check(nwii::runtime::post89_stop==1u&&nwii::runtime::async88_stop==1u&&nwii::runtime::async88_rfi==1u&&"
  ],
  [
    "V88_TRIAL_PASS trial=",
    "V89_TRIAL_PASS trial="
  ],
  [
    "V88 recovered continuous original __start->STM return after deferred ACK assertions",
    "V89 recovered continuous original __start->post STM console query assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V89 source anchor missing or ambiguous")
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
