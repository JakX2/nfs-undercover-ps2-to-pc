#!/usr/bin/env python3
"""V79 exact original-free generator patch: independent scheduler and RFI roots."""
import argparse
from pathlib import Path

EDITS = [
  [
    "0x80526a3cu,0x80519318u});",
    "0x80526a3cu,0x80519318u,0x80529940u,0x80529718u,0x805229b4u});"
  ],
  [
    "   for(uint32_t pc:{0x805293f8u,0x80529434u,0x80529940u})\n     require(funcs.count(pc)==1u,\"original external IRQ scheduler helper missing\");",
    "   for(uint32_t pc:{0x805293f8u,0x80529434u,0x80529940u})\n     require(funcs.count(pc)==1u,\"original external IRQ scheduler helper missing\");\n   const auto& reschedule=funcs.at(0x80529940u).instructions;\n   require(reschedule.front().address==0x80529940u&&reschedule.back().address<=0x80529954u,\n           \"V79 original reschedule body must not absorb SelectThread\");\n   const auto tail=std::find_if(reschedule.begin(),reschedule.end(),[](const auto& ins){return ins.address==0x80529950u;});\n   require(tail!=reschedule.end()&&tail->opcode>>26==18u&&!(tail->opcode&3u)&&\n           0x80529950u+(((tail->opcode&0x03fffffcu)^0x02000000u)-0x02000000u)==0x80529718u,\n           \"V79 authenticated reschedule tail missing\");\n   const auto& load_context=funcs.at(0x805229b4u).instructions;\n   require(load_context.front().address==0x805229b4u&&load_context.back().address<=0x80522a88u&&\n           std::any_of(load_context.begin(),load_context.end(),[](const auto& ins){\n             return ins.address==0x80522a88u&&ins.opcode==0x4c000064u;}),\n           \"V79 original context load RFI missing\");"
  ]
]

def derive(source):
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V79 generator source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
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
