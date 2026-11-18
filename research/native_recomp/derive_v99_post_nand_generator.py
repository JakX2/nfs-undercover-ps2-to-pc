#!/usr/bin/env python3
"""V99 original sibling generator guards."""
import argparse
from pathlib import Path
from derive_v97_es_close_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8052f94cu,0x8051e5bcu}){",
    "   require(funcs.count(0x8052f94cu)==1u,\"V99 original sibling missing\");\n   const auto& sibling=funcs.at(0x8052f94cu).instructions;\n   require(sibling.front().address==0x8052f94cu&&sibling.back().address==0x8052fa5cu&&\n           sibling.back().opcode==0x4e800020u&&sibling.size()>2u,\"V99 original sibling geometry differs\");\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,4>{{{0x8052f9e0u,0x8000443cu},\n        {0x8052f9f0u,0x80004338u},{0x8052fa00u,0x80004338u},{0x8052fa40u,0x8051dff4u}}}){\n     const auto it=std::find_if(sibling.begin(),sibling.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=sibling.end()&&branch(it->opcode,edge.first)==edge.second,\"V99 original sibling direct edge differs\");\n   }\n   for(uint32_t pc:{0x8051dff4u,0x8051e5bcu}){"
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
