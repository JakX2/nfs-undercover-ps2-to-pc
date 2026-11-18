#!/usr/bin/env python3
"""V102 original SC pathname generator geometry."""
import argparse
from pathlib import Path
from derive_v101_sc_loading_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051e71cu,0x8051e518u,0x8051e5bcu}){",
    "   for(const auto& [addr,size]:std::array<std::pair<uint32_t,uint32_t>,2>{{{0x8051e71cu,0xc8u},{0x80544ac0u,0x1cu}}}){\n     require(funcs.count(addr)==1u,\"V102 original pathname function missing\");\n     const auto& body=funcs.at(addr).instructions;\n     require(body.front().address==addr&&body.back().address==addr+size-4u&&\n             body.back().opcode==0x4e800020u,\"V102 original pathname geometry differs\");\n   }\n   const auto& sc_path=funcs.at(0x8051e71cu).instructions;\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,5>{{{0x8051e73cu,0x80544ac0u},\n        {0x8051e750u,0x8054b4b4u},{0x8051e788u,0x8051e3dcu},\n        {0x8051e798u,0x8054b4b4u},{0x8051e7a0u,0x80544ac0u}}}){\n     const auto it=std::find_if(sc_path.begin(),sc_path.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=sc_path.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V102 original pathname direct edge differs\");\n   }\n   for(uint32_t pc:{0x8051e3dcu,0x8051e518u,0x8051e5bcu}){"
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
