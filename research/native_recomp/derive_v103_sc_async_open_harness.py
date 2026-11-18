#!/usr/bin/env python3
"""V103 original system configuration asynchronous open wrapper."""
import argparse
from pathlib import Path
from derive_v102_sc_path_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x804f1e2cu",
    "POST_OWNER=0x8051982cu"
  ],
  [
    " static std::vector<uint8_t> post102_bytes;",
    " static std::vector<uint8_t> post102_bytes;\n static unsigned post103_save=0,post103_getter=0,post103_alloc=0,post103_alloc_tail=0;\n static unsigned post103_disable=0,post103_restore=0,post103_copy=0,post103_open=0;\n static uint32_t post103_dst=0;\n static std::vector<uint8_t> post103_bytes;"
  ],
  [
    "       if(addr==POST_OWNER&&ctx.lr==0x8051de3cu){",
    "       if(addr==0x804f1e2cu&&ctx.lr==0x8051de3cu){"
  ],
  [
    "         ++post102_verified;++post102_next;\n         post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};",
    "         ++post102_verified;++post102_next;return true; // execute original async file open wrapper"
  ],
  [
    "     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){",
    "     if(post102_next==1u){\n       if(addr==0x80545100u&&ctx.lr==0x804f1e40u){\n         const bool route=post103_save==0u&&post103_getter==0u&&ctx.msr==ipc69_msr&&\n              ctx.mmu.read16(THREAD+712u)==2u;\n         std::cout<<\"V103_SC_WRAPPER entry=\"<<route<<std::endl;\n         check(route,\"V103 original SC open wrapper GPR-save differs\");\n         ++post103_save;return true;\n       }\n       if(addr==0x80519094u&&ctx.lr==0x804f1e60u){\n         check(post103_save==1u&&post103_getter==0u&&ctx.msr==ipc69_msr,\n               \"V103 original SC resource getter ABI differs\");\n         ++post103_getter;return true;\n       }\n       if((addr==0x8051ad38u||addr==0x8051ab34u)&&ctx.lr==0x804f1e84u){\n         if(addr==0x8051ad38u){\n           check(post103_getter==1u&&post103_alloc==0u,\"V103 original SC open allocator entry differs\");\n           ++post103_alloc;\n         }else{\n           check(post103_alloc==1u&&post103_alloc_tail==0u,\"V103 original SC open allocator tail differs\");\n           ++post103_alloc_tail;\n         }\n         return true;\n       }\n       if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u){\n         check(post103_alloc_tail==1u&&post103_disable==0u&&ctx.msr==ipc69_msr,\n               \"V103 original SC allocator interrupt disable differs\");\n         ++post103_disable;return true;\n       }\n       if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u){\n         check(post103_disable==1u&&post103_restore==0u&&!(ctx.msr&0x8000u),\n               \"V103 original SC allocator interrupt restore differs\");\n         ++post103_restore;return true;\n       }\n       if(addr==COPY&&ctx.lr==0x804f1eb4u){\n         const uint32_t dest=ctx.gpr[3],src=ctx.gpr[4],n=ctx.gpr[5];\n         const bool range=post103_alloc==1u&&post103_copy==0u&&n>0u&&n<=0x1000u&&\n              open71_ram(dest,n)&&open71_ram(src,n)&&ctx.msr==ipc69_msr;\n         std::cout<<\"V103_SC_REQUEST_COPY range=\"<<range<<std::endl;\n         check(range,\"V103 original async request copy input differs\");\n         post103_dst=dest;post103_bytes.resize(n);\n         for(unsigned i=0;i<n;++i)post103_bytes[i]=ctx.mmu.read8(src+i);\n         ++post103_copy;return true;\n       }\n       if(addr==POST_OWNER&&ctx.lr==0x804f1eccu){\n         using I=undercover::wii::StmIos;\n         bool bytes=post103_copy==1u&&post103_bytes.size()>0u;\n         if(bytes)for(unsigned i=0;i<post103_bytes.size();++i)\n            bytes&=ctx.mmu.read8(post103_dst+i)==post103_bytes[i];\n         const uint32_t pathptr=ctx.gpr[3];\n         std::string name;bool valid=pathptr!=0u;\n         if(valid)for(unsigned i=0;i<64u;++i){\n           if(!open71_ram(pathptr+i,1u)){valid=false;break;}\n           const auto ch=ctx.mmu.read8(pathptr+i);\n           if(!ch)break;\n           name.push_back(char(ch));\n         }\n         valid&=name.size()>0u&&name.size()<64u;\n         const unsigned kind=name==\"/shared2/sys/SYSCONF\"?1u:\n             name==\"/title/00000001/00000002/data/setting.txt\"?2u:\n             name.starts_with(\"/shared2/\")?3u:name.starts_with(\"/\")?4u:0u;\n         const bool api=ctx.gpr[4]<=3u&&ctx.gpr[5]!=0u&&!(ctx.gpr[5]&3u)&&\n              ctx.gpr[5]>=0x80004000u&&ctx.gpr[5]<0x81800000u;\n         const bool route=post103_open==0u&&post103_save==1u&&post103_getter==1u&&\n              post103_alloc==1u&&post103_alloc_tail==1u&&post103_copy==1u&&bytes;\n         const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n              !ipc70_bus.services().is_open(3u,I::Device::Es)&&ipc70_bus.services().event_pending()&&\n              ipc70_bus.services().queued_replies()==0u;\n         std::cout<<\"V103_SC_ASYNC_OPEN route=\"<<route<<\" path=\"<<valid<<\" kind=\"<<kind\n                  <<\" api=\"<<api<<\" prior=\"<<prior<<std::endl;\n         check(route&&valid&&kind&&api&&prior,\"V103 original async file open did not reach native IOS API\");\n         ++post103_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n         throw ExceptionStop{};\n       }\n     }\n     if(addr==0x8051e5bcu&&ctx.lr==0x8051e8f8u){"
  ],
  [
    "     nwii::runtime::post102_bytes.clear();",
    "     nwii::runtime::post102_bytes.clear();\n     nwii::runtime::post103_save=nwii::runtime::post103_getter=nwii::runtime::post103_alloc=nwii::runtime::post103_alloc_tail=0;\n     nwii::runtime::post103_disable=nwii::runtime::post103_restore=nwii::runtime::post103_copy=nwii::runtime::post103_open=nwii::runtime::post103_dst=0;\n     nwii::runtime::post103_bytes.clear();"
  ],
  [
    "       check(nwii::runtime::post102_next==1u&&",
    "       check(nwii::runtime::post103_open==1u&&nwii::runtime::post102_next==1u&&"
  ],
  [
    "V102_TRIAL_PASS trial=",
    "V103_TRIAL_PASS trial="
  ],
  [
    "V102 recovered continuous original __start->SC pathname copy return assertions",
    "V103 recovered continuous original __start->SC async open wrapper entry assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V103 source anchor missing or ambiguous: "+old[:80])
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
