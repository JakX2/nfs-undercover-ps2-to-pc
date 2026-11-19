#!/usr/bin/env python3
"""V109: follow owner-authenticated nonempty SYSCONF pathname into genuine second copy."""
import argparse
from pathlib import Path
from derive_v108_sc_literal_restore_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x805195ecu",
    "POST_OWNER=0x80544ac0u"
  ],
  [
    " static bool post104_vector_active=false;",
    " static bool post104_vector_active=false;\n static uint32_t post109_dst=0;\n static unsigned post109_copy=0,post109_return=0;\n static std::vector<uint8_t> post109_expected;"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post101_child==1u&&post101_target==0x8051e71cu&&post102_strlen==1u){\n       if(addr==0x8054b4b4u&&ctx.lr==0x8051e79cu){\n         const uint32_t d=ctx.gpr[3],s=ctx.gpr[4];\n         bool valid=post109_copy==0u&&post102_copy==0u&&d!=0u&&s!=0u&&\n                    ctx.msr==ipc69_msr&&open71_ram(s,1u);\n         unsigned n=0u;\n         if(valid)for(;n<256u;++n){\n           if(!open71_ram(s+n,1u)){valid=false;break;}\n           if(ctx.mmu.read8(s+n)==0u)break;\n         }\n         // strcpy is valid for an empty, NUL-terminated input too.\n         // Do not infer its length from whether the owner pathname is nonempty.\n         const bool term=n<256u;\n         const bool output=term&&open71_ram(d,n+1u);\n         const bool order=post109_copy==0u&&post102_copy==0u;\n         const bool abi=ctx.msr==ipc69_msr;\n         const bool mapped=s!=0u&&open71_ram(s,1u);\n         std::cout<<\"V109_SC_SECOND_SOURCE order=\"<<order<<\" mapped=\"<<mapped\n                  <<\" terminated=\"<<term<<\" empty=\"<<(n==0u)\n                  <<\" output=\"<<output<<\" abi=\"<<abi<<std::endl;\n         valid&=term&&output;\n         std::cout<<\"V109_SC_SECOND_COPY input=\"<<valid<<\" bounded=\"<<term<<std::endl;\n         check(valid,\"V109 original nonempty SC second copy input differs\");\n         post109_dst=d;post109_expected.resize(n+1u);\n         for(unsigned i=0;i<=n;++i)post109_expected[i]=ctx.mmu.read8(s+i);\n         ++post109_copy;return true; // original PPC strcpy is executed\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x8051e7a4u){\n         bool data=post109_copy==1u&&post109_return==0u&&post109_dst!=0u&&\n                   !post109_expected.empty();\n         if(data)for(unsigned i=0;i<post109_expected.size();++i)\n           data&=ctx.mmu.read8(post109_dst+i)==post109_expected[i];\n         using I=undercover::wii::StmIos;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n             !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n             ipc70_bus.services().event_pending()&&\n             ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();\n         const bool route=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n             ctx.mmu.read16(THREAD+712u)==2u&&\n             ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n         std::cout<<\"V109_SC_NEXT_LENGTH route=\"<<route<<\" data=\"<<data\n                  <<\" prior=\"<<prior<<std::endl;\n         check(route&&data&&prior,\"V109 original nonempty SC copy did not reach next length helper\");\n         ++post109_return;post90_target=addr;observed_stop_pc=ctx.pc;\n         ++post_stops;ctx.is_running=false;throw ExceptionStop{};\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post104_vector=0;nwii::runtime::post104_vector_active=false;",
    "     nwii::runtime::post104_vector=0;nwii::runtime::post104_vector_active=false;\n     nwii::runtime::post109_dst=nwii::runtime::post109_copy=nwii::runtime::post109_return=0;\n     nwii::runtime::post109_expected.clear();"
  ],
  [
    "check(nwii::runtime::post104_submit==1u&&nwii::runtime::post103_async==1u&&nwii::runtime::post102_next==1u&&",
    "check(nwii::runtime::post109_return==1u&&nwii::runtime::post109_copy==1u&&nwii::runtime::post102_copy==0u&&"
  ],
  [
    "V104_TRIAL_PASS trial=",
    "V109_TRIAL_PASS trial="
  ],
  [
    "V104 recovered continuous original __start->IOS_OpenAsync request submit assertions",
    "V109 recovered continuous original __start->nonempty SC second string copy assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V109 nonempty SC native source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":main()
