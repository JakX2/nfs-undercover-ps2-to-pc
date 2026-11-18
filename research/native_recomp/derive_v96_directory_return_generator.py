#!/usr/bin/env python3
"""V96 original directory wrapper guard."""
import argparse
from pathlib import Path
from derive_v95_title_return_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x8051e5bcu}){",
    "   require(funcs.count(0x804f0ad8u)==1u,\"V96 original directory query wrapper missing\");\n   const auto& dir_query=funcs.at(0x804f0ad8u).instructions;\n   require(dir_query.front().address==0x804f0ad8u&&dir_query.back().address==0x804f0b6cu&&\n           dir_query.back().opcode==0x4e800020u&&dir_query.size()>2u,\"V96 directory wrapper geometry differs\");\n   const auto dir_call=std::find_if(dir_query.begin(),dir_query.end(),[](const auto& ins){return ins.address==0x804f0b58u;});\n   require(dir_call!=dir_query.end()&&branch(dir_call->opcode,0x804f0b58u)==0x8051a62cu,\"V96 directory query edge differs\");\n   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V96 source anchor missing or ambiguous: "+old[:80])
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
