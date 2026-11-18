#!/usr/bin/env python3
"""V86: original async STM wrapper to genuine IPC submission entry."""
import argparse
from pathlib import Path
from derive_v85_both_stm_opens_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x805265acu",
    "POST_OWNER=0x805195ecu"
  ],
  [
    " static unsigned open85_complete=0;",
    " static unsigned open85_complete=0;\n static unsigned async86_enter=0,async86_alloc=0,async86_disable=0,async86_restore=0,\n                 async86_flush=0,async86_sc=0,async86_submit=0;\n static uint32_t async86_fd=0,async86_in=0,async86_inlen=0,async86_out=0,async86_outlen=0;\n static uint32_t async86_flush_addr=0,async86_flush_len=0;\n static uint64_t async86_flush_before=0;\n static bool async86_in_flushed=false,async86_out_flushed=false;"
  ],
  [
    "     if(open84_active&&addr==POST_OWNER&&ctx.lr==0x8052b0d4u){",
    "     if(open84_active&&addr==INT_DISABLE&&ctx.lr==0x8052b0d4u){"
  ],
  [
    "       const bool route=ctx.pc==POST_OWNER&&open85_complete==0u&&stm70_open==2u;",
    "       const bool route=ctx.pc==INT_DISABLE&&open85_complete==0u&&stm70_open==2u;"
  ],
  [
    "       ++open85_complete;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original STM post-open interrupt disable",
    "       ++open85_complete;return true; // execute original STM post-open interrupt disable"
  ],
  [
    "   if(resume82_stop==1u&&(!open84_active||open84_ack==1u)){",
    "   if(open85_complete==1u){\n     using I=undercover::wii::StmIos;\n     if(addr==0x8051a1a4u){\n       const auto event_fd=open84_first_device==I::Device::Event?0u:1u;\n       bool callback_text=false;\n       for(const auto& sec:stm70_owner->sections)\n         if(sec.is_text&&!sec.is_bss&&sec.address<=ctx.gpr[9]&&\n            uint64_t(ctx.gpr[9])+4u<=uint64_t(sec.address)+sec.data.size())callback_text=true;\n       const bool route=async86_enter==0u&&ctx.lr==0x8052b108u&&ctx.gpr[1]==open71_stack&&\n                        !(ctx.msr&0x8000u)&&ctx.mmu.read32(0x800000e4u)==THREAD;\n       const bool service=ctx.gpr[3]==event_fd&&ctx.gpr[4]==I::EventHook&&\n                          ipc70_bus.services().is_open(event_fd,I::Device::Event);\n       const bool buffers=ctx.gpr[6]<=0x1000u&&(!ctx.gpr[6]||\n                          (ctx.gpr[5]&&open71_ram(ctx.gpr[5],ctx.gpr[6])))&&\n                          ctx.gpr[7]&&ctx.gpr[8]>=4u&&ctx.gpr[8]<=0x1000u&&\n                          open71_ram(ctx.gpr[7],ctx.gpr[8]);\n       const bool callback=ctx.gpr[9]&&!(ctx.gpr[9]&3u)&&callback_text;\n       const bool idle=!ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u&&\n                       !ipc70_bus.services().event_pending();\n       std::cout<<\"V86_ASYNC_ENTRY route=\"<<route<<\" service=\"<<service<<\" buffers=\"<<buffers\n                <<\" callback=\"<<callback<<\" idle=\"<<idle<<std::endl;\n       check(route&&service&&buffers&&callback&&idle,\"V86 original STM async event request ABI differs\");\n       async86_fd=ctx.gpr[3];async86_in=ctx.gpr[5]&0x3fffffffu;\n       async86_inlen=ctx.gpr[6];async86_out=ctx.gpr[7]&0x3fffffffu;async86_outlen=ctx.gpr[8];\n       async86_in_flushed=async86_inlen==0u;async86_out_flushed=false;\n       ++async86_enter;return true;\n     }\n     check(async86_enter==1u&&!(ctx.msr&0x8000u),\"V86 unexpected asynchronous startup call state\");\n     if(addr==0x805450f4u){\n       check(ctx.lr==0x8051a1b8u&&ctx.gpr[1]<open71_stack,\"V86 async register save helper differs\");\n       return true;\n     }\n     if(addr==0x8051ad38u){\n       check(ctx.lr==0x8051a1fcu&&async86_alloc==0u,\"V86 async allocator tail call differs\");\n       return true;\n     }\n     if(addr==0x8051ab34u){\n       check(ctx.lr==0x8051a1fcu&&async86_alloc==0u&&ctx.gpr[4]>=64u&&ctx.gpr[4]<=0x1000u,\n             \"V86 async request allocator ABI differs\");\n       ++async86_alloc;return true;\n     }\n     if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u){\n       check(async86_alloc==1u&&async86_disable==0u,\"V86 async allocation interrupt disable differs\");\n       ++async86_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u){\n       check(async86_disable==1u&&async86_restore==0u&&ctx.gpr[3]==0u,\n             \"V86 async allocation interrupt restore differs\");\n       ++async86_restore;return true;\n     }\n     if(addr==0x805222c0u){\n       check((ctx.lr==0x8051a29cu||ctx.lr==0x8051a2a8u)&&async86_alloc==1u&&\n             async86_restore==1u&&async86_flush==async86_sc&&async86_flush<2u&&\n             ctx.gpr[4]<=0x100000u&&(!ctx.gpr[4]||open71_ram(ctx.gpr[3],ctx.gpr[4])),\n             \"V86 original async cache flush ABI differs\");\n       async86_flush_addr=ctx.gpr[3];async86_flush_len=ctx.gpr[4];\n       async86_flush_before=ctx.guest_flush_count;\n       const uint32_t lo=async86_flush_addr&0x3fffffffu;\n       const uint64_t end=uint64_t(lo)+async86_flush_len;\n       async86_in_flushed|=lo<=async86_in&&end>=uint64_t(async86_in)+async86_inlen;\n       async86_out_flushed|=lo<=async86_out&&end>=uint64_t(async86_out)+async86_outlen;\n       ++async86_flush;return true;\n     }\n     if(addr==0x80000c00u){\n       check((ctx.lr==0x8051a29cu||ctx.lr==0x8051a2a8u)&&async86_flush==async86_sc+1u&&\n             ctx.srr0==0x805222ecu,\"V86 async flush did not enter original cache syscall vector\");\n       return true;\n     }\n     if(addr==POST_OWNER){\n       unsigned matches=0;\n       for(unsigned reg=3;reg<=10;++reg){\n         const uint32_t p=ctx.gpr[reg]&0x3fffffffu;\n         if(!ctx.gpr[reg]||(p&31u)||!ipc70_ram.valid(p,64u))continue;\n         if(ipc70_ram.read32(p)==I::Ioctl&&ipc70_ram.read32(p+8u)==async86_fd&&\n            ipc70_ram.read32(p+12u)==I::EventHook&&\n            (ipc70_ram.read32(p+16u)&0x3fffffffu)==async86_in&&\n            ipc70_ram.read32(p+20u)==async86_inlen&&\n            (ipc70_ram.read32(p+24u)&0x3fffffffu)==async86_out&&\n            ipc70_ram.read32(p+28u)==async86_outlen)++matches;\n       }\n       const bool route=ctx.pc==POST_OWNER&&ctx.lr==0x8051a2bcu&&async86_submit==0u&&\n                        ctx.gpr[1]<open71_stack;\n       const bool allocated=async86_alloc==1u&&async86_disable==1u&&async86_restore==1u;\n       const bool flush=async86_flush>0u&&async86_flush==async86_sc&&async86_in_flushed&&async86_out_flushed;\n       const bool wire=matches>0u;\n       const bool idle=!ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u&&\n                       !ipc70_bus.services().event_pending();\n       std::cout<<\"V86_ASYNC_SUBMIT route=\"<<route<<\" allocated=\"<<allocated<<\" flush=\"<<flush\n                <<\" wire=\"<<wire<<\" idle=\"<<idle<<std::endl;\n       check(route&&allocated&&flush&&wire&&idle,\"V86 original STM async request did not reach native submission\");\n       ++async86_submit;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original asynchronous submission\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V86_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     check(false,\"V86 unexpected original async wrapper dependency\");\n   }\n   if(resume82_stop==1u&&(!open84_active||open84_ack==1u)){"
  ],
  [
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){",
    "  if(own&&ctx.pc==0x805222e8u&&async86_enter==1u&&\n     (ctx.lr==0x8051a29cu||ctx.lr==0x8051a2a8u)){\n    check(async86_flush==async86_sc+1u,\"V86 async cache syscall order differs\");\n    const uint64_t lines=((async86_flush_addr&31u)+uint64_t(async86_flush_len)+31u)/32u;\n    check(ctx.guest_flush_count==async86_flush_before+lines,\"V86 async cache line count differs\");\n    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;const auto gp=ctx.gpr;\n    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),\n       [](auto& c){func_80000C00(c);});\n    check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\"V86 async cache syscall changed CPU state\");\n    for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)\n      check(ctx.gpr[r]==gp[r],\"V86 async cache syscall changed unrelated GPR\");\n    ++async86_sc;return true;\n  }\n  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){"
  ],
  [
    "     nwii::runtime::open84_active=false;nwii::runtime::open84_ack=0;nwii::runtime::open85_complete=0;",
    "     nwii::runtime::open84_active=false;nwii::runtime::open84_ack=0;nwii::runtime::open85_complete=0;\n     nwii::runtime::async86_enter=nwii::runtime::async86_alloc=nwii::runtime::async86_disable=0;\n     nwii::runtime::async86_restore=nwii::runtime::async86_flush=nwii::runtime::async86_sc=nwii::runtime::async86_submit=0;\n     nwii::runtime::async86_fd=nwii::runtime::async86_in=nwii::runtime::async86_inlen=0;\n     nwii::runtime::async86_out=nwii::runtime::async86_outlen=0;\n     nwii::runtime::async86_flush_addr=nwii::runtime::async86_flush_len=0;\n     nwii::runtime::async86_flush_before=0;\n     nwii::runtime::async86_in_flushed=nwii::runtime::async86_out_flushed=false;"
  ],
  [
    "       check(nwii::runtime::open85_complete==1u&&nwii::runtime::open84_active&&",
    "       check(nwii::runtime::async86_enter==1u&&nwii::runtime::async86_submit==1u&&\n             nwii::runtime::open85_complete==1u&&nwii::runtime::open84_active&&"
  ],
  [
    "V85_TRIAL_PASS trial=",
    "V86_TRIAL_PASS trial="
  ],
  [
    "V85 recovered continuous original __start->both STM opens completed assertions",
    "V86 recovered continuous original __start->asynchronous STM submission entry assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V86 source anchor missing or ambiguous")
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
