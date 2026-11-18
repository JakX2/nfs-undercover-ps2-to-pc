#!/usr/bin/env python3
"""V104 verify original IOS_OpenAsync request construction at native submit."""
import argparse
from pathlib import Path
from derive_v103_sc_async_entry_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051982cu",
    "POST_OWNER=0x805195ecu"
  ],
  [
    " static uint32_t post103_path=0,post103_mode=0,post103_callback=0,post103_copy_dst=0;",
    " static uint32_t post103_path=0,post103_mode=0,post103_callback=0,post103_copy_dst=0;\n static unsigned post104_save=0,post104_alloc_head=0,post104_alloc=0,post104_disable=0,post104_restore=0,post104_flush=0,post104_sc=0,post104_submit=0,post104_trace=0;\n static uint32_t post104_flush_base=0,post104_flush_len=0;\n static uint64_t post104_flush_before=0;\n static unsigned post104_vector=0;\n static bool post104_vector_active=false;"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x804f1eccu){",
    "       if(addr==0x8051982cu&&ctx.lr==0x804f1eccu){"
  ],
  [
    "         post103_path=ptr;post103_mode=mode;post103_callback=callback;++post103_async;\n         post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // stop before original IOS_OpenAsync request translation",
    "         post103_path=ptr;post103_mode=mode;post103_callback=callback;++post103_async;\n         return true; // execute authentic IOS_OpenAsync body"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post103_async==1u){\n       if(addr==0x80545104u&&ctx.lr==0x80519840u){\n         const bool ok=post104_save==0u&&ctx.msr==ipc69_msr&&\n              ctx.mmu.read16(THREAD+712u)==2u;\n         std::cout<<\"V104_ASYNC_SAVE route=\"<<ok<<std::endl;\n         check(ok,\"V104 original IOS_OpenAsync prologue differs\");\n         ++post104_save;return true;\n       }\n       if(addr==0x8051ad38u&&ctx.lr==0x80519874u){\n         check(post104_save==1u&&post104_alloc_head==0u&&post104_alloc==0u,\n               \"V104 original IOS_OpenAsync allocator wrapper differs\");\n         ++post104_alloc_head;return true;\n       }\n       if(addr==0x8051ab34u&&ctx.lr==0x80519874u){\n         check(post104_save==1u&&post104_alloc==0u&&ctx.gpr[4]>=64u&&\n               ctx.gpr[4]<=0x1000u&&ctx.msr==ipc69_msr,\n               \"V104 original IOS_OpenAsync allocation arguments differ\");\n         ++post104_alloc;return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post104_alloc==1u){\n         check(post104_disable==0u&&(ctx.msr&0x8000u),\n               \"V104 original IOS_OpenAsync allocator disable differs\");\n         ++post104_disable;return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post104_alloc==1u){\n         check(post104_disable==1u&&post104_restore==0u&&!(ctx.msr&0x8000u),\n               \"V104 original IOS_OpenAsync allocator restore differs\");\n         ++post104_restore;return true;\n       }\n       if(addr==0x805222c0u&&ctx.lr==0x80519904u){\n         const bool valid=post104_alloc==1u&&post104_restore==1u&&post104_flush==0u&&\n            ctx.gpr[3]!=0u&&ctx.gpr[4]>0u&&ctx.gpr[4]<=0x1000u&&\n            open71_ram(ctx.gpr[3],ctx.gpr[4])&&ctx.msr==ipc69_msr;\n         std::cout<<\"V104_ASYNC_CACHE bounded=\"<<valid<<std::endl;\n         check(valid,\"V104 original IOS_OpenAsync request cache flush differs\");\n         post104_flush_base=ctx.gpr[3];post104_flush_len=ctx.gpr[4];\n         post104_flush_before=ctx.guest_flush_count;\n         ++post104_flush;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x80519924u){\n         using I=undercover::wii::StmIos;\n         unsigned requests=0u,paths=0u,modes=0u;\n         for(unsigned reg=3u;reg<=10u;++reg){\n           const uint32_t p=ctx.gpr[reg]&0x3fffffffu;\n           if(!ctx.gpr[reg]||(p&31u)||!ipc70_ram.valid(p,64u))continue;\n           if(ipc70_ram.read32(p)!=I::Open)continue;\n           ++requests;\n           if(ipc70_ram.read32(p+16u)==post103_mode)++modes;\n           const uint32_t ptr=ipc70_ram.read32(p+12u)&0x3fffffffu;\n           bool path=ptr!=0u&&post102_bytes.size()>0u&&\n                post102_bytes.size()<=256u&&ipc70_ram.valid(ptr,uint32_t(post102_bytes.size()));\n           if(path)for(unsigned i=0;i<post102_bytes.size();++i)\n              path&=ipc70_ram.read8(ptr+i)==post102_bytes[i];\n           if(path)++paths;\n         }\n         const bool route=post104_submit==0u&&post104_save==1u&&post104_alloc==1u&&\n                post104_disable==1u&&post104_restore==1u&&post104_flush==1u&&post104_sc==1u;\n         const bool wire=requests>0u&&paths>0u&&modes>0u;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.mmu.read16(THREAD+712u)==2u&&\n                ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n                !ipc70_bus.services().is_open(3u,I::Device::Es)&&ipc70_bus.services().event_pending()&&\n                ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n         std::cout<<\"V104_ASYNC_SUBMIT route=\"<<route<<\" request=\"<<(requests>0u)\n                  <<\" mode=\"<<(modes>0u)<<\" path=\"<<(paths>0u)\n                  <<\" abi=\"<<abi<<\" prior=\"<<prior<<std::endl;\n         check(route&&wire&&abi&&prior,\n               \"V104 original IOS_OpenAsync did not construct native IPC request\");\n         ++post104_submit;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // at authentic IPC submission, before guest callback\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post103_path=nwii::runtime::post103_mode=nwii::runtime::post103_callback=nwii::runtime::post103_copy_dst=0;",
    "     nwii::runtime::post103_path=nwii::runtime::post103_mode=nwii::runtime::post103_callback=nwii::runtime::post103_copy_dst=0;\n     nwii::runtime::post104_save=nwii::runtime::post104_alloc_head=nwii::runtime::post104_alloc=nwii::runtime::post104_disable=nwii::runtime::post104_restore=nwii::runtime::post104_flush=nwii::runtime::post104_sc=nwii::runtime::post104_submit=nwii::runtime::post104_trace=0;\n     nwii::runtime::post104_flush_base=nwii::runtime::post104_flush_len=0;\n     nwii::runtime::post104_flush_before=0;\n     nwii::runtime::post104_vector=0;nwii::runtime::post104_vector_active=false;"
  ],
  [
    "       check(nwii::runtime::post103_async==1u&&",
    "       check(nwii::runtime::post104_submit==1u&&nwii::runtime::post103_async==1u&&"
  ],
  [
    "V103_TRIAL_PASS trial=",
    "V104_TRIAL_PASS trial="
  ],
  [
    "V103 recovered continuous original __start->SC asynchronous open entry assertions",
    "V104 recovered continuous original __start->IOS_OpenAsync request submit assertions"
  ],
  [
    "       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post103_alloc==1u){",
    "       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post103_alloc==1u&&post103_async==0u){"
  ],
  [
    "       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post103_alloc==1u){",
    "       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post103_alloc==1u&&post103_async==0u){"
  ],
  [
    "  if(own&&post95_active&&ctx.pc==0x805222e8u&&(ctx.lr==0x8051a474u||ctx.lr==0x8051a4ccu||ctx.lr==0x8051a514u)){",
    "  if(own&&post103_async==1u&&ctx.pc==0x805222e8u&&ctx.lr==0x80519904u){\n    const bool order=post104_flush==1u&&post104_sc==0u;\n    const uint64_t lines=((post104_flush_base&31u)+uint64_t(post104_flush_len)+31u)/32u;\n    const bool count=ctx.guest_flush_count==post104_flush_before+lines;\n    std::cout<<\"V104_ASYNC_SYSCALL order=\"<<order<<\" lines=\"<<count<<std::endl;\n    check(order&&count,\"V104 IOS_OpenAsync native cache syscall order or line count differs\");\n    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;\n    const auto gp=ctx.gpr;\n    check(!post104_vector_active&&post104_vector==0u,\"V104 syscall vector already active\");\n    post104_vector_active=true;\n    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),[](auto& c){func_80000C00(c);});\n    post104_vector_active=false;\n    check(post104_vector==1u,\"V104 genuine installed native syscall vector was not entered\");\n    check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\n          \"V104 IOS_OpenAsync native cache syscall state changed\");\n    for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)\n      check(ctx.gpr[r]==gp[r],\"V104 IOS_OpenAsync cache syscall changed unrelated GPR\");\n    ++post104_sc;return true;\n  }\n  if(own&&post95_active&&ctx.pc==0x805222e8u&&(ctx.lr==0x8051a474u||ctx.lr==0x8051a4ccu||ctx.lr==0x8051a514u)){"
  ],
  [
    "     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V98_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;",
    "     if(post103_async==1u){\n       std::cout<<\"V104_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V98_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;"
  ],
  [
    "     check(false,\"V98 unexpected NAND registration dependency\");",
    "     std::cout<<\"V104_FALLTHROUGH pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec\n              <<\" phase=\"<<post103_async<<\" cache=\"<<post104_sc<<std::endl;\n     check(false,\"V98 unexpected NAND registration dependency\");"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post103_async==1u&&post104_trace<24u){\n     ++post104_trace;\n     std::cout<<\"V104_TRACE seq=\"<<post104_trace<<\" pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n   }"
  ],
  [
    "void check(bool result,const char*why){if(!result)throw std::runtime_error(why);++checks;}",
    "static uint32_t v104_last_hook=0,v104_last_lr=0;\nvoid check(bool result,const char*why){\n  if(!result){\n    if(std::strcmp(why,\"V98 unexpected NAND registration dependency\")==0)\n      std::cout<<\"V104_FAIL_HOOK pc=\"<<std::hex<<v104_last_hook<<\" lr=\"<<v104_last_lr<<std::dec<<std::endl;\n    throw std::runtime_error(why);\n  }\n  ++checks;\n}"
  ],
  [
    "void trace_call(uint32_t addr, CPUContext&ctx){",
    "void trace_call(uint32_t addr, CPUContext&ctx){\n   v104_last_hook=addr;v104_last_lr=ctx.lr;"
  ],
  [
    "bool handle_syscall(CPUContext&ctx){",
    "bool handle_syscall(CPUContext&ctx){\n  v104_last_hook=ctx.pc;v104_last_lr=ctx.lr;"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post104_vector_active&&addr==SYSCALL_DEST){\n     const bool valid=ctx.lr==0x80519904u&&post104_vector==0u&&\n                      post104_flush==1u&&post104_sc==0u;\n     std::cout<<\"V104_ASYNC_VECTOR route=\"<<valid<<std::endl;\n     check(valid,\"V104 original installed syscall vector entry differs\");\n     ++post104_vector;return true; // original native vector executes normally\n   }"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V104 source anchor missing or ambiguous: "+old[:80])
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
