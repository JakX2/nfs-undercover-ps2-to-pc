#!/usr/bin/env python3
"""V89 exact original post-STM generator guard."""
import argparse
from pathlib import Path
from derive_v86_stm_ioctl_generator import derive as previous
EDITS = [
  [
    "OS_RET_STOP=0x80520968",
    "OS_RET_STOP=0x8052096c"
  ],
  [
    "           os_has(OS_RET_STOP,0x44000002u)&&os_has(0x8052097cu,0x44000002u) &&",
    "           os[190].address==0x80520968u&&branch(os[190].opcode,0x80520968u)==0x8052f790u&&\n           os_has(OS_RET_STOP,0x44000002u)&&os_has(0x8052097cu,0x44000002u) &&"
  ],
  [
    "           os_has(OS_RET_STOP,0x44000002u)&&os_has(0x8052097cu,0x44000002u),",
    "           os[190].address==0x80520968u&&branch(os[190].opcode,0x80520968u)==0x8052f790u&&\n           os_has(OS_RET_STOP,0x44000002u)&&os_has(0x8052097cu,0x44000002u),"
  ],
  [
    "   const auto& async_ioctl=funcs.at(0x8051a1a4u).instructions;",
    "   require(funcs.count(0x8052f790u)==1u,\"V89 original post-STM subsystem missing\");\n   const auto& post_stm=funcs.at(0x8052f790u).instructions;\n   require(post_stm.front().address==0x8052f790u&&post_stm.back().address==0x8052f82cu&&\n           post_stm.back().opcode==0x4e800020u,\"V89 original next subsystem body incomplete\");\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,8>{{\n       {0x8052f7a0u,0x805265acu},{0x8052f7b0u,0x805265d4u},{0x8052f7c4u,0x805265d4u},\n       {0x8052f7ccu,0x80521018u},{0x8052f7d8u,0x805293b0u},{0x8052f7dcu,0x8051fd44u},\n       {0x8052f7ecu,0x8051e7e4u},{0x8052f808u,0x8052f94cu}}}){\n     const auto it=std::find_if(post_stm.begin(),post_stm.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=post_stm.end()&&branch(it->opcode,edge.first)==edge.second,\"V89 original subsystem call edge differs\");\n   }\n   for(uint32_t pc:{0x8051e7e4u,0x8052f94cu}){\n     require(funcs.count(pc)==1u,\"V89 missing explicit next boundary\");\n     const auto& body=funcs.at(pc).instructions;\n     require(body.size()==2u&&body.front().opcode==0x44000002u&&body.back().opcode==0x4e800020u,\n             \"V89 unimplemented next dependency must remain explicit\");\n   }\n   const auto& async_ioctl=funcs.at(0x8051a1a4u).instructions;"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V89 source anchor missing or ambiguous")
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
