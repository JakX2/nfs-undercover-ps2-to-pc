#!/usr/bin/env python3
"""V95 original synchronous vector body guards."""
import argparse
from pathlib import Path
from derive_v94_es_open_generator import derive as previous
EDITS = [
  [
    "   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x8051e5bcu,0x8051a62cu}){",
    "   for(const auto& [pc,n]:std::array<std::pair<uint32_t,uint32_t>,2>{{{0x8051a62cu,0xdcu},{0x8051a40cu,0x13cu}}}){\n     require(funcs.count(pc)==1u,\"V95 original vector body missing\");\n     const auto& body=funcs.at(pc).instructions;\n     require(body.front().address==pc&&body.back().address==pc+n-4u&&\n             body.back().opcode==0x4e800020u&&body.size()>2u,\"V95 original vector body geometry differs\");\n   }\n   for(uint32_t pc:{0x8052f94cu,0x804f063cu,0x804f0ad8u,0x8051e5bcu}){"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V95 source anchor missing or ambiguous: "+old[:80])
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
