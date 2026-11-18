#!/usr/bin/env python3
"""V104 original IOS_OpenAsync generator geometry and dependency assertions."""
import argparse
from pathlib import Path
from derive_v103_sc_async_entry_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8051982cu,0x8051e3dcu,0x8051e518u,0x8051e5bcu}){",
    "   require(funcs.count(0x8051982cu)==1u,\"V104 original IOS_OpenAsync function missing\");\n   const auto& async_open=funcs.at(0x8051982cu).instructions;\n   require(async_open.front().address==0x8051982cu&&async_open.back().address==0x80519940u&&\n           async_open.back().opcode==0x4e800020u&&async_open.size()>2u,\n           \"V104 IOS_OpenAsync original geometry differs\");\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,5>{{{0x8051983cu,0x80545104u},\n        {0x80519870u,0x8051ad38u},{0x80519900u,0x805222c0u},\n        {0x80519920u,0x805195ecu},{0x80519930u,0x80545150u}}}){\n     const auto it=std::find_if(async_open.begin(),async_open.end(),[&](const auto& ins){return ins.address==edge.first;});\n     require(it!=async_open.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V104 authentic IOS_OpenAsync dependency differs\");\n   }\n   for(uint32_t pc:{0x8051e3dcu,0x8051e518u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V104 source anchor missing or ambiguous: "+old[:80])
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
