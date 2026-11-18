#!/usr/bin/env python3
"""V93 original next service wrapper generator guard."""
import argparse
from pathlib import Path
from derive_v91_resource_open_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8052f94cu,0x804f05e8u,0x804f063cu,0x804f0ad8u,0x804f0b70u,0x8051e5bcu}){",
    "   require(funcs.count(0x804f05e8u)==1u,\"V93 original next resource wrapper missing\");\n   const auto& next_resource=funcs.at(0x804f05e8u).instructions;\n   require(next_resource.front().address==0x804f05e8u&&next_resource.back().address==0x804f0638u&&\n           next_resource.back().opcode==0x4e800020u&&next_resource.size()>2u,\n           \"V93 original next resource wrapper geometry differs\");\n   const auto next_call=std::find_if(next_resource.begin(),next_resource.end(),\n                                   [](const auto& ins){return ins.address==0x804f0610u;});\n   require(next_call!=next_resource.end()&&branch(next_call->opcode,0x804f0610u)==0x80519944u,\n           \"V93 original next service open call edge differs\");\n   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x804f0b70u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V93 source anchor missing or ambiguous")
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
