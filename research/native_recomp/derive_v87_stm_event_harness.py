#!/usr/bin/env python3
"""V87: original async submission and deferred native STM event registration."""
import argparse
from pathlib import Path
from derive_v86_stm_ioctl_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x805195ecu",
    "POST_OWNER=0x805265d4u"
  ],
  [
    " static bool async86_in_flushed=false,async86_out_flushed=false;",
    " static bool async86_in_flushed=false,async86_out_flushed=false;\n static unsigned async87_init=0,async87_flush=0,async87_sc=0,async87_disable=0,async87_queue=0,\n                 async87_msg=0,async87_x1=0,async87_restore=0,async87_tail=0,async87_deferred=0;\n static uint32_t async87_request=0,async87_flush_base=0,async87_flush_len=0;\n static uint64_t async87_flush_before=0;"
  ],
  [
    "     if(addr==POST_OWNER){\n       unsigned matches=0;",
    "     if(addr==0x805195ecu&&async86_submit==0u){\n       unsigned matches=0;"
  ],
  [
    "            ipc70_ram.read32(p+28u)==async86_outlen)++matches;",
    "            ipc70_ram.read32(p+28u)==async86_outlen){\n           check(!async87_request||async87_request==p,\"V87 ambiguous async request pointer\");\n           async87_request=p;++matches;\n         }"
  ],
  [
    "       const bool route=ctx.pc==POST_OWNER&&ctx.lr==0x8051a2bcu&&async86_submit==0u&&",
    "       const bool route=ctx.pc==0x805195ecu&&ctx.lr==0x8051a2bcu&&async86_submit==0u&&"
  ],
  [
    "       ++async86_submit;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original asynchronous submission",
    "       ++async86_submit;return true; // execute real async IPC submission"
  ],
  [
    "     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V86_DEPENDENCY",
    "     if(async86_submit==1u){\n       using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n       using H=undercover::wii::HollywoodIrq;\n       if(addr==0x805293b0u){\n         check(ctx.lr==0x80519630u&&async87_init==0u&&open71_ram(ctx.gpr[3],8u),\n               \"V87 async queue initializer call differs\");\n         ++async87_init;return true;\n       }\n       if(addr==0x805222c0u&&ctx.lr==0x8051963cu){\n         check(async87_flush==0u&&open71_ram(ctx.gpr[3],ctx.gpr[4])&&\n               ctx.gpr[4]>=32u&&ctx.gpr[4]<=0x1000u,\"V87 async request header flush differs\");\n         async87_flush_base=ctx.gpr[3];async87_flush_len=ctx.gpr[4];\n         async87_flush_before=ctx.guest_flush_count;++async87_flush;return true;\n       }\n       if(addr==0x80000c00u&&ctx.lr==0x8051963cu){\n         check(async87_flush==1u&&async87_sc==0u&&ctx.srr0==0x805222ecu,\n               \"V87 async submission cache syscall route differs\");\n         return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x80519640u){\n         check(async87_sc==1u&&async87_disable==0u,\"V87 async submit interrupt disable differs\");\n         ++async87_disable;return true;\n       }\n       if(addr==0x8051afe0u){\n         check(ctx.lr==0x805196d4u&&async87_disable==1u&&async87_queue==0u,\n               \"V87 async queue helper call differs\");\n         ++async87_queue;return true;\n       }\n       if(addr==0x8051905cu||addr==0x8051906cu){\n         check(async87_disable==1u&&(ctx.lr==0x80519780u||ctx.lr==0x805197b8u||ctx.lr==0x805197c8u),\n               \"V87 async register helper call differs\");\n         return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x805197e0u){\n         check(async87_x1==1u&&async87_restore==0u&&ctx.gpr[3]==0u,\n               \"V87 async submission restore did not preserve disabled caller\");\n         ++async87_restore;return true;\n       }\n       if(addr==0x80545140u){\n         check(ctx.lr==0x8051a2ccu&&async87_restore==1u&&async87_tail==0u&&ctx.gpr[3]==0u,\n               \"V87 asynchronous wrapper return ABI differs\");\n         ++async87_tail;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x8052b128u){\n         const bool descriptors=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n              ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n         const bool route=ctx.pc==POST_OWNER&&async87_tail==1u&&async87_deferred==0u&&\n              ctx.gpr[1]==open71_stack&&!(ctx.msr&0x8000u)&&ctx.gpr[3]!=0u;\n         const bool thread=ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n                           ctx.mmu.read32(0x800000e4u)==THREAD;\n         const uint32_t lo=async87_flush_base&0x3fffffffu;\n         const bool sent=async87_queue==1u&&async87_msg==1u&&async87_x1==1u&&async87_sc==1u&&\n              lo<=async87_request&&uint64_t(lo)+async87_flush_len>=uint64_t(async87_request)+32u&&\n              ipc70_bus.read32(B::IPC+M::PPCMSG)==async87_request;\n         const bool before=!ipc70_bus.external_irq_level()&&!ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u&&ipc70_ram.read32(async87_request)==I::Ioctl;\n         std::cout<<\"V87_ASYNC_RETURN route=\"<<route<<\" descriptors=\"<<descriptors<<\" thread=\"<<thread\n                  <<\" sent=\"<<sent<<\" before=\"<<before<<std::endl;\n         check(route&&descriptors&&thread&&sent&&before,\"V87 async IPC did not return with an actual submitted request\");\n         check(ipc70_bus.tick()==I::Pump::Deferred,\"V87 native STM service did not defer event hook\");\n         const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(0u);\n         const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG).value_or(0u);\n         const bool pending=ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u;\n         const bool ack=(ctrl&(M::X1|M::Y1|M::Y2))==M::Y2&&(flag&H::IPC_PPC)&&\n              ipc70_bus.external_irq_level()&&!ipc70_bus.external_exception_pending(ctx.msr);\n         const bool wire=ipc70_ram.read32(async87_request)==I::Ioctl&&\n              ipc70_ram.read32(async87_request+8u)==async86_fd&&\n              ipc70_ram.read32(async87_request+12u)==I::EventHook;\n         std::cout<<\"V87_DEFERRED pending=\"<<pending<<\" ack=\"<<ack<<\" wire=\"<<wire<<std::endl;\n         check(pending&&ack&&wire,\"V87 async event registration mutated or prematurely completed request\");\n         ++async87_deferred;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // before original STM outer interrupt restore\n       }\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V86_DEPENDENCY"
  ],
  [
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){",
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu&&async86_submit==1u){\n    check(async87_flush==1u&&async87_sc==0u,\"V87 async request cache syscall order differs\");\n    const uint64_t lines=((async87_flush_base&31u)+uint64_t(async87_flush_len)+31u)/32u;\n    check(ctx.guest_flush_count==async87_flush_before+lines,\"V87 async request cache line count differs\");\n    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;const auto gp=ctx.gpr;\n    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),\n       [](auto& c){func_80000C00(c);});\n    check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\"V87 async request cache syscall changed CPU state\");\n    for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)\n      check(ctx.gpr[r]==gp[r],\"V87 async request cache syscall changed unrelated GPR\");\n    ++async87_sc;return true;\n  }\n  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){"
  ],
  [
    "uint32_t HW_Reg_Read32(uint32_t addr){\n   if(submit72_active){",
    "uint32_t HW_Reg_Read32(uint32_t addr){\n   if(async86_submit==1u){\n     const auto value=ipc70_bus.read32(addr);\n     check(value.has_value(),\"V87 unsupported async IPC register read\");\n     mmio_reads.emplace_back(addr,*value);return *value;\n   }\n   if(submit72_active){"
  ],
  [
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(irq76_ipc&&(!open84_active||open84_ack==1u)){",
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(async86_submit==1u){\n     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n     const bool msg=addr==B::IPC+M::PPCMSG||addr==B::MIRROR+M::PPCMSG;\n     const bool ctrl=addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL;\n     check(ipc70_ram.cpu&&!(ipc70_ram.cpu->msr&0x8000u),\"V87 async mailbox write outside masked submit\");\n     if(msg){\n       check(async87_msg==0u&&value==async87_request,\"V87 async PPCMSG did not select actual request\");\n       ++async87_msg;\n     }else if(ctrl){\n       check(async87_msg==1u&&async87_x1==0u&&(value&M::X1),\n             \"V87 async PPCCTRL did not submit actual request\");\n       ++async87_x1;\n     }else check(false,\"V87 unexpected async IPC register write\");\n     check(ipc70_bus.write32(addr,value),\"V87 native IOS bus rejected async request\");\n     mmio_writes.emplace_back(addr,value);return;\n   }\n   if(irq76_ipc&&(!open84_active||open84_ack==1u)){"
  ],
  [
    "     nwii::runtime::async86_in_flushed=nwii::runtime::async86_out_flushed=false;",
    "     nwii::runtime::async86_in_flushed=nwii::runtime::async86_out_flushed=false;\n     nwii::runtime::async87_init=nwii::runtime::async87_flush=nwii::runtime::async87_sc=0;\n     nwii::runtime::async87_disable=nwii::runtime::async87_queue=nwii::runtime::async87_msg=0;\n     nwii::runtime::async87_x1=nwii::runtime::async87_restore=nwii::runtime::async87_tail=nwii::runtime::async87_deferred=0;\n     nwii::runtime::async87_request=nwii::runtime::async87_flush_base=nwii::runtime::async87_flush_len=0;\n     nwii::runtime::async87_flush_before=0;"
  ],
  [
    "       check(nwii::runtime::async86_enter==1u&&nwii::runtime::async86_submit==1u&&",
    "       check(nwii::runtime::async87_deferred==1u&&nwii::runtime::async86_enter==1u&&nwii::runtime::async86_submit==1u&&"
  ],
  [
    "V86_TRIAL_PASS trial=",
    "V87_TRIAL_PASS trial="
  ],
  [
    "V86 recovered continuous original __start->asynchronous STM submission entry assertions",
    "V87 recovered continuous original __start->asynchronous STM event registration assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V87 source anchor missing or ambiguous")
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
