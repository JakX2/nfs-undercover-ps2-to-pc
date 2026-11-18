#!/usr/bin/env python3
"""V102 verified original SC pathname preparation."""
import argparse
from pathlib import Path
from derive_v101_sc_loading_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051e71cu",
    "POST_OWNER=0x804f1e2cu"
  ],
  [
    " static uint32_t post101_target=0;",
    " static uint32_t post101_target=0;\n static unsigned post102_strlen=0,post102_copy=0,post102_verified=0,post102_next=0;\n static uint32_t post102_dst=0;\n static std::vector<uint8_t> post102_bytes;"
  ],
  [
    "         ++post101_child;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{}; // before executing original child selected by original conditions",
    "         ++post101_child;return true; // execute original selected SC pathname child"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post101_child==1u&&post101_target==0x8051e71cu){\n       if(addr==0x80544ac0u&&ctx.lr==0x8051e740u){\n         const uint32_t s=ctx.gpr[3];\n         bool valid=s!=0u&&open71_ram(s,1u)&&post102_strlen==0u&&ctx.msr==ipc69_msr;\n         unsigned len=0u;\n         if(valid)for(;len<256u;++len){\n           if(!open71_ram(s+len,1u)){valid=false;break;}\n           if(ctx.mmu.read8(s+len)==0u)break;\n         }\n         valid&=len<256u;\n         std::cout<<\"V102_SC_STRLEN input=\"<<valid<<\" bounded=\"<<(len<256u)<<std::endl;\n         check(valid,\"V102 original SC pathname length input differs\");\n         ++post102_strlen;return true;\n       }\n       if(addr==0x8054b4b4u&&ctx.lr==0x8051e754u){\n         const uint32_t d=ctx.gpr[3],s=ctx.gpr[4];\n         bool valid=post102_strlen==1u&&post102_copy==0u&&d!=0u&&s!=0u&&ctx.msr==ipc69_msr;\n         unsigned len=0u;\n         if(valid)for(;len<256u;++len){\n           if(!open71_ram(s+len,1u)){valid=false;break;}\n           if(ctx.mmu.read8(s+len)==0u)break;\n         }\n         valid&=len<256u&&open71_ram(d,len+1u);\n         std::cout<<\"V102_SC_COPY input=\"<<valid<<\" bounded=\"<<(len<256u)<<std::endl;\n         check(valid,\"V102 original SC pathname copy input differs\");\n         post102_dst=d;post102_bytes.resize(len+1u);\n         for(unsigned i=0;i<=len;++i)post102_bytes[i]=ctx.mmu.read8(s+i);\n         ++post102_copy;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x8051de3cu){\n         using I=undercover::wii::StmIos;\n         bool bytes=post102_copy==1u&&post102_bytes.size()>0u;\n         if(bytes)for(unsigned i=0;i<post102_bytes.size();++i)\n           bytes&=ctx.mmu.read8(post102_dst+i)==post102_bytes[i];\n         const bool route=post102_next==0u&&post102_strlen==1u&&post102_copy==1u&&bytes;\n         const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<post98_root_stack&&\n              ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&\n              ctx.mmu.read32(0x800000e4u)==THREAD;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&\n              ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u;\n         std::cout<<\"V102_SC_PATH route=\"<<route<<\" bytes=\"<<bytes<<\" abi=\"<<abi\n                  <<\" prior=\"<<prior<<std::endl;\n         check(route&&abi&&prior,\"V102 original SC pathname did not reach asynchronous file open wrapper\");\n         ++post102_verified;++post102_next;\n         post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post101_save=nwii::runtime::post101_child=nwii::runtime::post101_target=0;",
    "     nwii::runtime::post101_save=nwii::runtime::post101_child=nwii::runtime::post101_target=0;\n     nwii::runtime::post102_strlen=nwii::runtime::post102_copy=nwii::runtime::post102_verified=nwii::runtime::post102_next=nwii::runtime::post102_dst=0;\n     nwii::runtime::post102_bytes.clear();"
  ],
  [
    "       check(nwii::runtime::post101_child==1u&&",
    "       check(nwii::runtime::post102_next==1u&&nwii::runtime::post101_child==1u&&"
  ],
  [
    "V101_TRIAL_PASS trial=",
    "V102_TRIAL_PASS trial="
  ],
  [
    "V101 recovered continuous original __start->SC configuration child entry assertions",
    "V102 recovered continuous original __start->SC pathname copy return assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V102 source anchor missing or ambiguous: "+old[:80])
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
