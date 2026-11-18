#!/usr/bin/env python3
"""V101 original SC configuration body guards."""
import argparse
from pathlib import Path
from derive_v100_sc_status_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051dd50u,0x8051e5bcu}){",
    "   require(funcs.count(0x8051dd50u)==1u,\"V101 original SC configuration body missing\");\n   const auto& sc=funcs.at(0x8051dd50u).instructions;\n   require(sc.front().address==0x8051dd50u&&sc.back().address==0x8051de60u&&\n           sc.back().opcode==0x4e800020u&&sc.size()>2u,\n           \"V101 original SC configuration body geometry differs\");\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,6>{{{0x8051dd60u,0x80545104u},\n        {0x8051ddc4u,0x8051e71cu},{0x8051ddd4u,0x8051e518u},\n        {0x8051de38u,0x804f1e2cu},{0x8051de48u,0x804f1d64u},\n        {0x8051de50u,0x80545150u}}}){\n     const auto it=std::find_if(sc.begin(),sc.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=sc.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V101 original SC configuration direct edge differs\");\n   }\n   for(uint32_t pc:{0x8051e71cu,0x8051e518u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V101 source anchor missing or ambiguous: "+old[:80])
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
