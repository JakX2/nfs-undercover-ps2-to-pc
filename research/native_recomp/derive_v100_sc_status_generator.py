#!/usr/bin/env python3
"""V100 original SC status body guards."""
import argparse
from pathlib import Path
from derive_v99_post_nand_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051dff4u,0x8051e5bcu}){",
    "   for(const auto& [addr,size]:std::array<std::pair<uint32_t,uint32_t>,2>{{{0x8051dff4u,0x78u},{0x8051e5a4u,0x14u}}}){\n     require(funcs.count(addr)==1u,\"V100 original SC status body missing\");\n     const auto& body=funcs.at(addr).instructions;\n     require(body.front().address==addr&&body.back().address==addr+size-4u&&\n             body.back().opcode==0x4e800020u&&body.size()>2u,\"V100 original SC status body geometry differs\");\n   }\n   const auto& status=funcs.at(0x8051dff4u).instructions;\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,5>{{{0x8051e004u,0x80545104u},\n        {0x8051e01cu,0x8051e5a4u},{0x8051e04cu,0x8051dd50u},\n        {0x8051e050u,0x8051e5bcu},{0x8051e058u,0x80545150u}}}){\n     const auto it=std::find_if(status.begin(),status.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=status.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V100 original SC status edge differs\");\n   }\n   for(uint32_t pc:{0x8051dd50u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V100 source anchor missing or ambiguous: "+old[:80])
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
