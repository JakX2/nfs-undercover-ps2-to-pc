#!/usr/bin/env python3
"""V88: genuine active-thread IRQ, RFI and STM return to original OSInit."""
import argparse
from pathlib import Path
from derive_v87_stm_event_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x805265d4u",
    "POST_OWNER=0x80520968u"
  ],
  [
    " static uint64_t async87_flush_before=0;",
    " static uint64_t async87_flush_before=0;\n static unsigned async88_irq=0,async88_vector=0,async88_handler=0,async88_dispatch=0,\n                 async88_time=0,async88_disable=0,async88_ipc=0,async88_ctrl=0,async88_flag=0,\n                 async88_reads=0,async88_enable=0,async88_reschedule=0,async88_load=0,\n                 async88_rfi=0,async88_stop=0,async88_pi_cause=0,async88_pi_mask=0;\n static uint32_t async88_resume=0,async88_msr=0,async88_lr=0,async88_ctr=0,async88_xer=0;\n static std::array<uint32_t,32> async88_gprs{};"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x8052b128u){",
    "       if(addr==INT_RESTORE&&ctx.lr==0x8052b128u){"
  ],
  [
    "         const bool route=ctx.pc==POST_OWNER&&async87_tail==1u&&async87_deferred==0u&&",
    "         const bool route=ctx.pc==INT_RESTORE&&async87_tail==1u&&async87_deferred==0u&&"
  ],
  [
    "         ++async87_deferred;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // before original STM outer interrupt restore",
    "         ++async87_deferred;return true; // execute original outer restore and sample genuine pending IRQ"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " // Transaction 3 differs from the synchronous opens: the original\n // running thread is interrupted directly. Its context must be saved and\n // restored by the original vector and dispatcher, with no sleep/wakeup.\n static bool async88_trace(uint32_t addr,CPUContext&ctx){\n   using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n   using H=undercover::wii::HollywoodIrq;using I=undercover::wii::StmIos;\n   const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n             ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n   const bool masked=!(ctx.msr&B::MSR_EE);\n   if(addr==0x80000500u){\n     check(async88_irq==1u&&async88_vector==0u&&ctx.pc==addr&&ctx.srr0==async88_resume&&\n           ctx.srr1==async88_msr&&ctx.gpr==async88_gprs&&ctx.lr==async88_lr&&\n           ctx.ctr==async88_ctr&&ctx.xer==async88_xer&&masked&&running,\n           \"V88 active thread external-vector entry state differs\");\n     for(unsigned i=0;i<irq74_vector.size();++i)\n       check(ctx.mmu.read8(addr+i)==irq74_vector[i],\"V88 original vector bytes changed\");\n     ++async88_vector;return true;\n   }\n   if(addr==0x80526ce0u){\n     const bool route=async88_vector==1u&&async88_handler==0u&&ctx.gpr[3]==4u&&ctx.gpr[4]==THREAD;\n     const bool saved=ctx.mmu.read32(THREAD+408u)==async88_resume&&\n          ctx.mmu.read32(THREAD+412u)==async88_msr&&ctx.mmu.read32(THREAD+132u)==async88_lr&&\n          ctx.mmu.read32(THREAD+136u)==async88_ctr&&ctx.mmu.read32(THREAD+140u)==async88_xer&&\n          ctx.mmu.read32(THREAD+12u)==async88_gprs[3]&&ctx.mmu.read32(THREAD+16u)==async88_gprs[4]&&\n          ctx.mmu.read32(THREAD+20u)==async88_gprs[5];\n     std::cout<<\"V88_ACTIVE_VECTOR route=\"<<route<<\" saved=\"<<saved<<\" running=\"<<running\n              <<\" masked=\"<<masked<<std::endl;\n     check(route&&saved&&running&&masked,\"V88 active original context was not saved by external vector\");\n     ++async88_handler;return true;\n   }\n   if(addr==0x80526a3cu){\n     check(async88_handler==1u&&async88_dispatch==0u&&ctx.gpr[3]==4u&&ctx.gpr[4]==THREAD&&masked,\n           \"V88 original interrupt trampoline route differs\");\n     for(unsigned r=6;r<32u;++r)\n       check(ctx.mmu.read32(THREAD+4u*r)==async88_gprs[r],\"V88 original IRQ body lost interrupted GPR\");\n     ++async88_dispatch;return true;\n   }\n   if(addr==0x8052a824u){\n     check(async88_dispatch==1u&&async88_time==0u&&ctx.lr==0x80526c84u&&masked,\n           \"V88 active IRQ timebase call differs\");\n     ++async88_time;return true;\n   }\n   if(addr==0x805293f8u){\n     check(async88_time==1u&&async88_disable==0u&&ctx.lr==0x80526c98u&&masked,\n           \"V88 active IRQ scheduler disable differs\");\n     ++async88_disable;return true;\n   }\n   if(addr==INT_DISABLE||addr==INT_RESTORE){\n     const bool disable=async88_disable==1u&&ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u;\n     const bool enable=async88_enable==1u&&(ctx.lr==0x80529448u||ctx.lr==0x80529458u);\n     if(disable||enable){check(masked,\"V88 nested scheduler helper unmasked unexpectedly\");return true;}\n   }\n   if(addr==0x80519318u){\n     const bool route=async88_disable==1u&&async88_ipc==0u&&ctx.gpr[3]==27u&&ctx.gpr[4]==THREAD&&\n          ctx.ctr==addr&&ctx.lr>=0x80526c98u&&ctx.lr<=0x80526cacu&&ipc69_handler==addr;\n     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(0u);\n     const bool pending=ipc70_bus.external_irq_level()&&(ctrl&(M::Y1|M::Y2))==M::Y2&&\n          ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n          ipc70_ram.read32(async87_request)==I::Ioctl;\n     check(route&&pending&&running&&masked&&async88_pi_cause>0u&&async88_pi_mask>0u,\n           \"V88 IRQ dispatcher did not select original deferred event ACK handler\");\n     ++async88_ipc;return true;\n   }\n   if(async88_ipc==1u&&(addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){\n     check(ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&masked,\"V88 original ACK leaf call differs\");\n     return true;\n   }\n   if(addr==0x80529434u){\n     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u);\n     const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG).value_or(~0u);\n     const bool clear=!(ctrl&(M::Y1|M::Y2|M::X1))&&!(flag&H::IPC_PPC)&&!ipc70_bus.external_irq_level();\n     const bool deferred=ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n                         ipc70_ram.read32(async87_request)==I::Ioctl;\n     const bool route=ctx.lr==0x80526cb0u&&async88_ipc==1u&&async88_enable==0u&&\n                      async88_reads>0u&&async88_ctrl>0u&&async88_flag>0u&&masked;\n     std::cout<<\"V88_ACTIVE_ACK clear=\"<<clear<<\" deferred=\"<<deferred<<\" running=\"<<running\n              <<\" route=\"<<route<<std::endl;\n     check(clear&&deferred&&running&&route,\"V88 original deferred ACK did not clear without completing event\");\n     check(ipc70_bus.tick()==I::Pump::Idle&&!ipc70_bus.external_irq_level(),\n           \"V88 deferred event unexpectedly generated immediate reply\");\n     ++async88_enable;return true;\n   }\n   if(addr==0x80529940u){\n     check(async88_enable==1u&&async88_reschedule==0u&&ctx.lr==0x80526cb4u&&masked,\n           \"V88 original active reschedule route differs\");\n     ++async88_reschedule;return true;\n   }\n   if(addr==0x80529718u){\n     check(async88_reschedule==1u&&ctx.gpr[3]==0u&&running&&masked,\n           \"V88 scheduler did not preserve running thread\");return true;\n   }\n   if(addr==0x80522928u){\n     check(async88_reschedule==1u&&ctx.lr==0x80529748u&&running&&masked,\n           \"V88 scheduler context getter differs\");return true;\n   }\n   if(addr==0x805229b4u){\n     const bool route=async88_enable==1u&&async88_reschedule==1u&&async88_load==0u&&\n        (ctx.lr==0x80526cbcu||ctx.lr==0x80526cc4u)&&ctx.gpr[3]==THREAD&&masked;\n     const bool saved=ctx.mmu.read32(THREAD+408u)==async88_resume&&\n                      ctx.mmu.read32(THREAD+412u)==async88_msr;\n     check(route&&saved&&running,\"V88 original IRQ did not load interrupted running context\");\n     ++async88_load;return true;\n   }\n   if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n     std::cout<<\"V88_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n   check(false,\"V88 unexpected active-thread IRQ dependency\");return false;\n }\n\n static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(async87_deferred==1u)return async88_trace(addr,ctx);"
  ],
  [
    "bool process_pending_callbacks(CPUContext& ctx){\n  if(resume82_idle_load",
    "bool process_pending_callbacks(CPUContext& ctx){\n  if(async87_deferred==1u){\n    using namespace undercover::wii;\n    if(async88_load==1u&&async88_rfi==0u&&ctx.pc==async88_resume){\n      const bool regs=ctx.gpr==async88_gprs&&ctx.lr==async88_lr&&ctx.ctr==async88_ctr&&ctx.xer==async88_xer;\n      const bool status=ctx.msr==async88_msr&&ctx.dispatch_saved_ctx==0u;\n      const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n           ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n      const bool deferred=ipc70_bus.services().event_pending()&&!ipc70_bus.external_irq_level()&&\n                          ipc70_bus.services().queued_replies()==0u;\n      std::cout<<\"V88_ACTIVE_RFI regs=\"<<regs<<\" status=\"<<status<<\" running=\"<<running\n               <<\" deferred=\"<<deferred<<std::endl;\n      check(regs&&status&&running&&deferred,\"V88 original RFI did not restore running thread\");\n      ++async88_rfi;\n    }\n    if(!ipc70_bus.external_exception_pending(ctx.msr))return false;\n    const bool route=async88_irq==0u&&ctx.lr==0x8052b128u&&ctx.pc>=0x805265d8u&&ctx.pc<0x805265f8u&&\n                     ctx.msr==ipc69_msr;\n    check(route&&ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n          ctx.mmu.read32(0x800000e4u)==THREAD,\"V88 active IRQ sampled outside original STM interrupt restore\");\n    const auto previous=original_word(ctx.pc-4u);\n    check(previous>>26==31u&&((previous>>1)&1023u)==146u,\"V88 active IRQ not sampled after genuine mtmsr\");\n    async88_resume=ctx.pc;async88_msr=ctx.msr;async88_lr=ctx.lr;async88_ctr=ctx.ctr;\n    async88_xer=ctx.xer;async88_gprs=ctx.gpr;\n    check(enter_external_irq(ctx,ipc70_bus,irq74_vector,true)==ExternalEntry::Entered,\n          \"V88 native deferred ACK did not enter installed original vector\");\n    check(ctx.srr0==async88_resume&&ctx.srr1==async88_msr&&ctx.pc==0x80000500u,\n          \"V88 native external entry lost active original resume PC\");\n    ++async88_irq;return true;\n  }\n  if(resume82_idle_load"
  ],
  [
    "bool handle_syscall(CPUContext&ctx){\n  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;",
    "bool handle_syscall(CPUContext&ctx){\n  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;\n  if(own&&async87_deferred==1u&&ctx.pc==POST_OWNER){\n    using I=undercover::wii::StmIos;using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n    const bool route=async88_rfi==1u&&async88_stop==0u&&ctx.lr==POST_OWNER&&ctx.gpr[1]==ipc69_gprs[1];\n    bool abi=ctx.msr==ipc69_msr&&ctx.gpr[2]==ipc69_gprs[2]&&ctx.gpr[13]==ipc69_gprs[13];\n    for(unsigned r=14;r<32u;++r)abi&=ctx.gpr[r]==ipc69_gprs[r];\n    const bool running=ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n                       ctx.mmu.read32(0x800000e4u)==THREAD;\n    const bool deferred=ipc70_bus.services().event_pending()&&ipc70_bus.services().queued_replies()==0u&&\n          ipc70_ram.read32(async87_request)==I::Ioctl&&!ipc70_bus.external_irq_level()&&\n          (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u)&(M::X1|M::Y1|M::Y2))==0u;\n    const bool devices=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n                       ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n    std::cout<<\"V88_STM_RETURN route=\"<<route<<\" abi=\"<<abi<<\" running=\"<<running\n             <<\" deferred=\"<<deferred<<\" devices=\"<<devices<<std::endl;\n    check(route&&abi&&running&&deferred&&devices,\"V88 original STM init did not return to OSInit\");\n    ++async88_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n    throw ExceptionStop{}; // existing owner-only stop at original OSInit next callsite\n  }"
  ],
  [
    "   if(async86_submit==1u){\n     const auto value=ipc70_bus.read32(addr);",
    "   if(async87_deferred==1u){\n     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n     const auto value=ipc70_bus.read32(addr);\n     check(value.has_value()&&async88_irq==1u,\"V88 unexpected active IRQ MMIO read\");\n     if(addr==B::PI_CAUSE)++async88_pi_cause;\n     if(addr==B::PI_MASK)++async88_pi_mask;\n     if(addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)++async88_reads;\n     mmio_reads.emplace_back(addr,*value);return *value;\n   }\n   if(async86_submit==1u){\n     const auto value=ipc70_bus.read32(addr);"
  ],
  [
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(async86_submit==1u){",
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(async87_deferred==1u){\n     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;using H=undercover::wii::HollywoodIrq;\n     check(async88_ipc==1u&&ipc70_ram.cpu&&!(ipc70_ram.cpu->msr&B::MSR_EE),\n           \"V88 active IRQ MMIO write outside masked handler\");\n     if(addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL){\n       check(!(value&(M::X1|M::Y1)),\"V88 deferred ACK unexpectedly issued request or reply clear\");\n       if(value&M::Y2)++async88_ctrl;\n     }else if(addr==B::IPC+H::PPC_FLAG||addr==B::MIRROR+H::PPC_FLAG){\n       check(value&H::IPC_PPC,\"V88 deferred IRQ flag write lacks W1C\");++async88_flag;\n     }else check(false,\"V88 unsupported deferred IRQ register write\");\n     check(ipc70_bus.write32(addr,value),\"V88 native bus rejected deferred ACK write\");\n     mmio_writes.emplace_back(addr,value);return;\n   }\n   if(async86_submit==1u){"
  ],
  [
    "     nwii::runtime::async87_flush_before=0;",
    "     nwii::runtime::async87_flush_before=0;\n     nwii::runtime::async88_irq=nwii::runtime::async88_vector=nwii::runtime::async88_handler=0;\n     nwii::runtime::async88_dispatch=nwii::runtime::async88_time=nwii::runtime::async88_disable=0;\n     nwii::runtime::async88_ipc=nwii::runtime::async88_ctrl=nwii::runtime::async88_flag=0;\n     nwii::runtime::async88_reads=nwii::runtime::async88_enable=nwii::runtime::async88_reschedule=0;\n     nwii::runtime::async88_load=nwii::runtime::async88_rfi=nwii::runtime::async88_stop=0;\n     nwii::runtime::async88_pi_cause=nwii::runtime::async88_pi_mask=0;\n     nwii::runtime::async88_resume=nwii::runtime::async88_msr=nwii::runtime::async88_lr=0;\n     nwii::runtime::async88_ctr=nwii::runtime::async88_xer=0;\n     nwii::runtime::async88_gprs.fill(0u);"
  ],
  [
    "       check(nwii::runtime::async87_deferred==1u&&nwii::runtime::async86_enter==1u&&",
    "       check(nwii::runtime::async88_stop==1u&&nwii::runtime::async88_rfi==1u&&\n             nwii::runtime::async87_deferred==1u&&nwii::runtime::async86_enter==1u&&"
  ],
  [
    "V87_TRIAL_PASS trial=",
    "V88_TRIAL_PASS trial="
  ],
  [
    "V87 recovered continuous original __start->asynchronous STM event registration assertions",
    "V88 recovered continuous original __start->STM return after deferred ACK assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V88 source anchor missing or ambiguous")
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
