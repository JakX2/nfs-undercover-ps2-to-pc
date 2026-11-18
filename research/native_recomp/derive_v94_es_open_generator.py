#!/usr/bin/env python3
"""V94 original title query wrapper generator guards."""
import argparse
from pathlib import Path
from derive_v93_isfs_return_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x804f0b70u,0x8051e5bcu}){",
    "   require(funcs.count(0x804f0b70u)==1u,\"V94 original title query wrapper missing\");\n   const auto& title_query=funcs.at(0x804f0b70u).instructions;\n   require(title_query.front().address==0x804f0b70u&&title_query.back().address==0x804f0c04u&&\n           title_query.back().opcode==0x4e800020u&&title_query.size()>2u,\n           \"V94 original title query wrapper geometry differs\");\n   const auto query_call=std::find_if(title_query.begin(),title_query.end(),\n                                   [](const auto& ins){return ins.address==0x804f0bd4u;});\n   require(query_call!=title_query.end()&&branch(query_call->opcode,0x804f0bd4u)==0x8051a62cu,\n           \"V94 original title query call edge differs\");\n   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x8051e5bcu,0x8051a62cu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V94 source anchor missing or ambiguous")
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
