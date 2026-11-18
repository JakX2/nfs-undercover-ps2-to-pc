#!/usr/bin/env python3
"""V103 original async open wrapper generator guards."""
import argparse
from pathlib import Path
from derive_v102_sc_path_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051e3dcu,0x8051e518u,0x8051e5bcu}){",
    "   for(const auto& [addr,size]:std::array<std::pair<uint32_t,uint32_t>,2>{{{0x804f1e2cu,0xb8u},{0x80519094u,0x2cu}}}){\n     require(funcs.count(addr)==1u,\"V103 original async wrapper body missing\");\n     const auto& body=funcs.at(addr).instructions;\n     require(body.front().address==addr&&body.back().address==addr+size-4u&&\n             body.back().opcode==0x4e800020u,\"V103 original async wrapper geometry differs\");\n   }\n   const auto& async_wrap=funcs.at(0x804f1e2cu).instructions;\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,6>{{{0x804f1e3cu,0x80545100u},\n        {0x804f1e5cu,0x80519094u},{0x804f1e80u,0x8051ad38u},\n        {0x804f1eb0u,0x80004338u},{0x804f1ec8u,0x8051982cu},\n        {0x804f1ed0u,0x8054514cu}}}){\n     const auto it=std::find_if(async_wrap.begin(),async_wrap.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=async_wrap.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V103 original async wrapper direct edge differs\");\n   }\n   for(uint32_t pc:{0x8051982cu,0x8051e3dcu,0x8051e518u,0x8051e5bcu}){"
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
