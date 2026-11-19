#!/usr/bin/env python3
"""V112 genuine original nonempty SC IOS_OpenAsync request construction."""
import argparse
from pathlib import Path
from derive_v111_sc_async_wrapper_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051982cu",
    "POST_OWNER=0x805195ecu"
  ],
  [
    " static uint32_t post111_copy_dst=0;",
    " static uint32_t post111_copy_dst=0;\n static unsigned post112_save=0,post112_alloc_head=0,post112_alloc=0,post112_disable=0,post112_restore=0,post112_flush=0,post112_sc=0,post112_vector=0,post112_submit=0;\n static uint32_t post112_mode=0,post112_flush_base=0,post112_flush_len=0;\n static uint64_t post112_flush_before=0;\n static bool post112_vector_active=false;\n static std::vector<uint8_t> post112_path;"
  ],
  [
    "         ++post111_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // observe, do not dispatch async IOS request yet",
    "         post112_mode=mode;post112_path.resize(n+1u);\n         for(unsigned i=0;i<=n;++i)post112_path[i]=ctx.mmu.read8(ptr+i);\n         ++post111_open;return true; // original IOS_OpenAsync is now executed"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post111_open==1u&&post110_chosen==2u){\n       using I=undercover::wii::StmIos;\n       if(post112_vector_active&&addr==SYSCALL_DEST){\n         check(ctx.lr==0x80519904u&&post112_flush==1u&&post112_vector==0u&&post112_sc==0u,\n               \"V112 original cache syscall vector entry differs\");\n         ++post112_vector;return true;\n       }\n       if(addr==0x80545104u&&ctx.lr==0x80519840u){\n         check(post112_save==0u&&ctx.msr==ipc69_msr&&ctx.mmu.read16(THREAD+712u)==2u,\n               \"V112 original IOS_OpenAsync GPR save differs\");\n         ++post112_save;return true;\n       }\n       if(addr==0x8051ad38u&&ctx.lr==0x80519874u){\n         check(post112_save==1u&&post112_alloc_head==0u,\n               \"V112 original IOS_OpenAsync allocation wrapper differs\");\n         ++post112_alloc_head;return true;\n       }\n       if(addr==0x8051ab34u&&ctx.lr==0x80519874u){\n         check(post112_alloc_head==1u&&post112_alloc==0u&&ctx.gpr[4]>=64u&&\n               ctx.gpr[4]<=0x1000u&&ctx.msr==ipc69_msr,\n               \"V112 original IOS_OpenAsync allocation arguments differ\");\n         ++post112_alloc;return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u&&post112_alloc==1u){\n         check(post112_disable==0u&&(ctx.msr&0x8000u),\n               \"V112 original IOS_OpenAsync allocator disable differs\");\n         ++post112_disable;return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u&&post112_alloc==1u){\n         check(post112_disable==1u&&post112_restore==0u&&!(ctx.msr&0x8000u),\n               \"V112 original IOS_OpenAsync allocator restore differs\");\n         ++post112_restore;return true;\n       }\n       if(addr==0x805222c0u&&ctx.lr==0x80519904u){\n         const bool bounded=post112_restore==1u&&post112_flush==0u&&ctx.gpr[3]!=0u&&\n               ctx.gpr[4]>0u&&ctx.gpr[4]<=0x1000u&&open71_ram(ctx.gpr[3],ctx.gpr[4]);\n         check(bounded,\"V112 original IOS_OpenAsync cache range differs\");\n         post112_flush_base=ctx.gpr[3];post112_flush_len=ctx.gpr[4];\n         post112_flush_before=ctx.guest_flush_count;\n         ++post112_flush;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x80519924u){\n         unsigned requests=0u,modes=0u,paths=0u;\n         for(unsigned reg=3u;reg<=10u;++reg){\n           const uint32_t p=ctx.gpr[reg]&0x3fffffffu;\n           if(!ctx.gpr[reg]||(p&31u)||!ipc70_ram.valid(p,64u))continue;\n           if(ipc70_ram.read32(p)!=I::Open)continue;\n           ++requests;\n           if(ipc70_ram.read32(p+16u)==post112_mode)++modes;\n           const uint32_t q=ipc70_ram.read32(p+12u)&0x3fffffffu;\n           bool path=q!=0u&&!post112_path.empty()&&post112_path.size()<=256u&&\n               ipc70_ram.valid(q,uint32_t(post112_path.size()));\n           if(path)for(unsigned i=0;i<post112_path.size();++i)\n              path&=ipc70_ram.read8(q+i)==post112_path[i];\n           if(path)++paths;\n         }\n         const bool route=post112_submit==0u&&post112_save==1u&&post112_alloc_head==1u&&\n              post112_alloc==1u&&post112_disable==1u&&post112_restore==1u&&\n              post112_flush==1u&&post112_sc==1u&&post112_vector==1u;\n         const bool wire=requests>0u&&modes>0u&&paths>0u;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.mmu.read16(THREAD+712u)==2u&&\n              ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n              ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n         std::cout<<\"V112_ASYNC_SUBMIT route=\"<<route<<\" wire=\"<<wire\n                  <<\" mode=\"<<(modes>0u)<<\" path=\"<<(paths>0u)<<\" abi=\"<<abi\n                  <<\" prior=\"<<prior<<std::endl;\n         check(route&&wire&&abi&&prior,\n               \"V112 original nonempty SC IOS_OpenAsync did not prepare request\");\n         ++post112_submit;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // stop before native IPC submission and callback\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "  if(own&&post103_async==1u&&ctx.pc==0x805222e8u&&ctx.lr==0x80519904u){",
    "  if(own&&post111_open==1u&&ctx.pc==0x805222e8u&&ctx.lr==0x80519904u){\n    const bool order=post112_flush==1u&&post112_sc==0u;\n    const uint64_t lines=((post112_flush_base&31u)+uint64_t(post112_flush_len)+31u)/32u;\n    const bool count=ctx.guest_flush_count==post112_flush_before+lines;\n    std::cout<<\"V112_ASYNC_SYSCALL order=\"<<order<<\" lines=\"<<count<<std::endl;\n    check(order&&count,\"V112 original IOS_OpenAsync native cache syscall differs\");\n    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;\n    const auto gp=ctx.gpr;\n    check(!post112_vector_active&&post112_vector==0u,\n          \"V112 original IOS_OpenAsync syscall vector already active\");\n    post112_vector_active=true;\n    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),\n                         [](auto& c){func_80000C00(c);});\n    post112_vector_active=false;\n    check(post112_vector==1u&&ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\n          \"V112 original IOS_OpenAsync syscall changed guest CPU state\");\n    for(unsigned reg=0;reg<32u;++reg)if(reg!=9u&&reg!=10u)\n      check(ctx.gpr[reg]==gp[reg],\"V112 original IOS_OpenAsync syscall changed unrelated GPR\");\n    ++post112_sc;return true;\n  }\n  if(own&&post103_async==1u&&ctx.pc==0x805222e8u&&ctx.lr==0x80519904u){"
  ],
  [
    "     nwii::runtime::post111_copy_expected.clear();",
    "     nwii::runtime::post111_copy_expected.clear();\n     nwii::runtime::post112_save=nwii::runtime::post112_alloc_head=nwii::runtime::post112_alloc=nwii::runtime::post112_disable=nwii::runtime::post112_restore=nwii::runtime::post112_flush=nwii::runtime::post112_sc=nwii::runtime::post112_vector=nwii::runtime::post112_submit=0;\n     nwii::runtime::post112_mode=nwii::runtime::post112_flush_base=nwii::runtime::post112_flush_len=0;\n     nwii::runtime::post112_flush_before=0;nwii::runtime::post112_vector_active=false;\n     nwii::runtime::post112_path.clear();"
  ],
  [
    "check(nwii::runtime::post111_open==1u&&",
    "check(nwii::runtime::post112_submit==1u&&nwii::runtime::post111_open==1u&&"
  ],
  [
    "     check(false,\"V98 unexpected NAND registration dependency\");",
    "     if(post111_open==1u&&post110_chosen==2u&&addr>=0x80004000u&&addr<0x80600000u&&\n        ctx.lr>=0x80004000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V112_BOUNDARY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec\n                <<\" save=\"<<post112_save<<\" alloc=\"<<post112_alloc<<\" restore=\"<<post112_restore\n                <<\" flush=\"<<post112_flush<<\" sc=\"<<post112_sc<<\" vector=\"<<post112_vector<<std::endl;\n     check(false,\"V98 unexpected NAND registration dependency\");"
  ],
  [
    "V111_TRIAL_PASS trial=",
    "V112_TRIAL_PASS trial="
  ],
  [
    "V111 recovered continuous original __start->nonempty SC IOS_OpenAsync entry assertions",
    "V112 recovered continuous original __start->nonempty SC IOS_OpenAsync request assertions"
  ]
]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:raise ValueError("V112 source anchor missing or ambiguous: "+old[:90])
        source=source.replace(old,new,1)
    return source
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
