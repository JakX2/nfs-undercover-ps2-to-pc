#!/usr/bin/env python3
"""V90: original console classification selects its actual next dependency."""
import argparse
from pathlib import Path
from derive_v89_post_stm_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051fd44u",
    "POST_OWNER=0x8052f94cu"
  ],
  [
    " static uint32_t post89_version_ptr=0,post89_queue_ptr=0;",
    " static uint32_t post89_version_ptr=0,post89_queue_ptr=0;\n static unsigned post90_mem2=0,post90_route=0;\n static uint32_t post90_target=0;"
  ],
  [
    "   if(addr==POST_OWNER&&ctx.lr==0x8052f7e0u){",
    "   if(addr==0x8051fd44u&&ctx.lr==0x8052f7e0u){"
  ],
  [
    "     ++post89_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // exact original console classification entry",
    "     ++post89_stop;return true; // run authentic console type helper\n   }\n   if(addr==0x8052701cu){\n     check(post89_stop==1u&&post90_mem2==0u&&ctx.lr==0x8051fec8u&&\n          report_trial%4u!=0u&&ctx.msr==ipc69_msr,\n          \"V90 original console-type native MEM2 query differs\");\n     ++post90_mem2;return true;\n   }\n   if(addr==0x8051e7e4u||addr==POST_OWNER){\n     const bool first=addr==0x8051e7e4u;\n     const bool route=post89_stop==1u&&post90_route==0u&&ctx.pc==addr&&\n            ctx.lr==(first?0x8052f7f0u:0x8052f80cu);\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]<ipc69_gprs[1]&&\n            ctx.gpr[2]==ipc69_gprs[2]&&ctx.gpr[13]==ipc69_gprs[13];\n     const bool console=post90_mem2<=1u&&(report_trial%4u!=0u||post90_mem2==0u);\n     const bool queue=ctx.mmu.read32(post89_queue_ptr)==0u&&ctx.mmu.read32(post89_queue_ptr+4u)==0u;\n     const bool devices=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n           ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n     std::cout<<\"V90_CONSOLE_ROUTE route=\"<<route<<\" abi=\"<<abi<<\" console=\"<<console\n              <<\" queue=\"<<queue<<\" devices=\"<<devices<<\" pending=\"<<pending<<std::endl;\n     check(route&&abi&&console&&queue&&devices&&pending,\"V90 original console branch did not reach a genuine subsystem dependency\");\n     post90_target=addr;++post90_route;\n     std::cout<<\"V90_ROUTE_TARGET mode=\"<<report_trial%4u<<\" pc=\"<<std::hex<<addr<<std::dec<<std::endl;\n     observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // genuine next original child, not a completed stub"
  ],
  [
    "     nwii::runtime::post89_version_ptr=nwii::runtime::post89_queue_ptr=0;",
    "     nwii::runtime::post89_version_ptr=nwii::runtime::post89_queue_ptr=0;\n     nwii::runtime::post90_mem2=nwii::runtime::post90_route=0;nwii::runtime::post90_target=0;"
  ],
  [
    "    if(nwii::runtime::observed_stop_pc!=(owner?POST_OWNER:POST_SYNTH) || c.is_running)",
    "    if(nwii::runtime::observed_stop_pc!=(owner?nwii::runtime::post90_target:POST_SYNTH) || c.is_running)"
  ],
  [
    "    check(!c.is_running && nwii::runtime::observed_stop_pc==(owner?POST_OWNER:POST_SYNTH),",
    "    check(!c.is_running && nwii::runtime::observed_stop_pc==(owner?nwii::runtime::post90_target:POST_SYNTH),"
  ],
  [
    "       check(nwii::runtime::post89_stop==1u&&",
    "       check(nwii::runtime::post90_route==1u&&(nwii::runtime::post90_target==0x8051e7e4u||nwii::runtime::post90_target==POST_OWNER)&&\n             nwii::runtime::post89_stop==1u&&"
  ],
  [
    "V89_TRIAL_PASS trial=",
    "V90_TRIAL_PASS trial="
  ],
  [
    "V89 recovered continuous original __start->post STM console query assertions",
    "V90 recovered continuous original __start->post STM original dependency assertions"
  ],
  [
    "<<std::hex<<(owner?POST_OWNER:POST_SYNTH)<<std::dec<<\"\\n\";",
    "<<std::hex<<(owner?nwii::runtime::post90_target:POST_SYNTH)<<std::dec<<\"\\n\";"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V90 source anchor missing or ambiguous")
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
