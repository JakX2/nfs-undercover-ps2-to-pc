#!/usr/bin/env python3
"""V91 original resource initializer generator guards."""
import argparse
from pathlib import Path
from derive_v89_post_stm_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051e7e4u,0x8052f94cu}){",
    "   for(const auto& [pc,size]:std::array<std::pair<uint32_t,uint32_t>,3>{{\n       {0x8051e7e4u,0x12cu},{0x804f0cdcu,0x128u},{0x8054b4b4u,0xc0u}}}){\n     require(funcs.count(pc)==1u,\"V91 restored original resource function missing\");\n     const auto& body=funcs.at(pc).instructions;\n     require(body.front().address==pc&&body.back().address==pc+size-4u&&\n             body.back().opcode==0x4e800020u&&body.size()>2u,\"V91 original resource function geometry differs\");\n   }\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,8>{{\n       {0x804f0d00u,0x80519084u},{0x804f0d08u,0x8051907cu},{0x804f0d48u,0x80522f00u},\n       {0x804f0d58u,0x8054b4b4u},{0x804f0d64u,0x80519944u},{0x804f0da8u,0x80522f00u},\n       {0x804f0dc0u,0x8051908cu},{0x804f0dd4u,0x8051aa04u}}}){\n     const auto& body=funcs.at(0x804f0cdcu).instructions;\n     const auto it=std::find_if(body.begin(),body.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=body.end()&&branch(it->opcode,edge.first)==edge.second,\"V91 original resource initializer edge differs\");\n   }\n   for(uint32_t pc:{0x8052f94cu,0x804f05e8u,0x804f063cu,0x804f0ad8u,0x804f0b70u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V91 source anchor missing or ambiguous")
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
