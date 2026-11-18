#!/usr/bin/env python3
"""V99 original post-NAND memory helper verification."""
import argparse
from pathlib import Path
from derive_v98_nand_registration_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8052f94cu",
    "POST_OWNER=0x8051dff4u"
  ],
  [
    " static unsigned post98_disable=0,post98_restore=0,post98_version=0,post98_report=0,post98_return=0;",
    " static unsigned post98_disable=0,post98_restore=0,post98_version=0,post98_report=0,post98_return=0;\n static unsigned post99_set=0,post99_fill=0,post99_copy=0,post99_verified=0,post99_return=0;\n static uint32_t post99_dst=0;\n static std::vector<uint8_t> post99_expected;"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static void post99_verify_memory(CPUContext&ctx){\n   if(post99_expected.empty())return;\n   for(unsigned i=0;i<post99_expected.size();++i)\n     check(ctx.mmu.read8(post99_dst+i)==post99_expected[i],\"V99 original memory helper output differs\");\n   post99_expected.clear();++post99_verified;\n }\n static bool submit72_trace(uint32_t addr,CPUContext&ctx){"
  ],
  [
    "     if(addr==POST_OWNER&&ctx.lr==0x8052f80cu){",
    "     if(addr==0x8052f94cu&&ctx.lr==0x8052f80cu){"
  ],
  [
    "       ++post98_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{};",
    "       ++post98_return;return true; // execute original sibling after authenticated NAND return"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post98_return==1u){\n       if(addr==SET&&ctx.lr==0x8052f9e4u){\n         check(post99_set==0u&&post99_copy==0u&&post99_expected.empty()&&ctx.msr==ipc69_msr&&\n               ctx.gpr[5]>0u&&ctx.gpr[5]<=0x100000u&&open71_ram(ctx.gpr[3],ctx.gpr[5]),\n               \"V99 original sibling memset ABI differs\");\n         post99_dst=ctx.gpr[3];post99_expected.assign(ctx.gpr[5],uint8_t(ctx.gpr[4]));\n         ++post99_set;return true;\n       }\n       if(addr==FILL&&ctx.lr==0x80004454u){\n         check(post99_set==1u&&post99_fill==0u&&ctx.msr==ipc69_msr,\"V99 original memset helper edge differs\");\n         ++post99_fill;return true;\n       }\n       if(addr==COPY&&(ctx.lr==0x8052f9f4u||ctx.lr==0x8052fa04u)){\n         post99_verify_memory(ctx);\n         check(post99_set==1u&&post99_fill==1u&&post99_copy<2u&&\n               ctx.lr==(post99_copy?0x8052fa04u:0x8052f9f4u)&&ctx.msr==ipc69_msr&&\n               ctx.gpr[5]>0u&&ctx.gpr[5]<=0x100000u&&open71_ram(ctx.gpr[3],ctx.gpr[5])&&open71_ram(ctx.gpr[4],ctx.gpr[5]),\n               \"V99 original sibling copy ABI differs\");\n         post99_dst=ctx.gpr[3];const uint32_t src=ctx.gpr[4],n=ctx.gpr[5];\n         // Only restore an omitted immutable initialized input span at its\n         // actual guest address, not stack/BSS data and not any destination.\n         bool zero=true;\n         for(unsigned i=0;i<n;++i)zero&=ctx.mmu.read8(src+i)==0u;\n         if(zero)(void)seed_stm_data(ctx,src,n);\n         post99_expected.resize(n);\n         for(unsigned i=0;i<n;++i)post99_expected[i]=ctx.mmu.read8(src+i);\n         ++post99_copy;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x8052fa44u){\n         post99_verify_memory(ctx);\n         const bool route=post99_return==0u&&post99_set==1u&&post99_fill==1u&&post99_copy==2u&&post99_verified==3u;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&ctx.mmu.read16(THREAD+712u)==2u&&\n                        ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool data=ctx.mmu.read32(R13-3176u)!=0u&&ctx.mmu.read32(R13-3584u)!=0u&&\n                         ctx.mmu.read32(R13-16768u)==2u&&ctx.mmu.read32(R13-16784u)==0xffffffffu;\n         std::cout<<\"V99_SIBLING_MEMORY route=\"<<route<<\" abi=\"<<abi<<\" data=\"<<data<<\" prior=\"<<prior<<std::endl;\n         check(route&&abi&&data,\"V99 original post NAND sibling did not reach next helper\");\n         ++post99_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post98_disable=nwii::runtime::post98_restore=nwii::runtime::post98_version=nwii::runtime::post98_report=nwii::runtime::post98_return=0;",
    "     nwii::runtime::post98_disable=nwii::runtime::post98_restore=nwii::runtime::post98_version=nwii::runtime::post98_report=nwii::runtime::post98_return=0;\n     nwii::runtime::post99_set=nwii::runtime::post99_fill=nwii::runtime::post99_copy=nwii::runtime::post99_verified=nwii::runtime::post99_return=nwii::runtime::post99_dst=0;\n     nwii::runtime::post99_expected.clear();"
  ],
  [
    "       check(nwii::runtime::post98_return==1u&&",
    "       check(nwii::runtime::post99_return==1u&&nwii::runtime::post98_return==1u&&"
  ],
  [
    "V98_TRIAL_PASS trial=",
    "V99_TRIAL_PASS trial="
  ],
  [
    "V98 recovered continuous original __start->NAND callback registration assertions",
    "V99 recovered continuous original __start->post NAND memory helper assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V99 source anchor missing or ambiguous: "+old[:80])
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
