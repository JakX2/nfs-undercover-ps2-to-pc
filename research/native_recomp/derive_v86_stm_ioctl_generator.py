#!/usr/bin/env python3
"""V86 generator guard for the original async IOS body, never a syscall stub."""
import argparse
from pathlib import Path
from derive_v79_reply_generator import derive as previous

OLD="   for(uint32_t pc:{0x8051a1a4u}){\n     const auto& boundary=funcs.at(pc).instructions;\n     require(boundary.size()==2u&&boundary.front().opcode==0x44000002u&&boundary.back().opcode==0x4e800020u,\n             \"IOS boundary must remain explicitly synthetic\");\n   }"
NEW="   const auto& async_ioctl=funcs.at(0x8051a1a4u).instructions;\n   require(!async_ioctl.empty()&&async_ioctl.front().address==0x8051a1a4u&&\n           async_ioctl.back().address<=0x8051a2d8u&&async_ioctl.size()>2u,\n           \"V86 authenticated asynchronous IOS body missing\");\n   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,6>{{\n       {0x8051a1b4u,0x805450f4u},{0x8051a1f8u,0x8051ad38u},\n       {0x8051a298u,0x805222c0u},{0x8051a2a4u,0x805222c0u},\n       {0x8051a2b8u,0x805195ecu},{0x8051a2c8u,0x80545140u}}}){\n     const auto it=std::find_if(async_ioctl.begin(),async_ioctl.end(),\n          [&](const auto& ins){return ins.address==edge.first;});\n     require(it!=async_ioctl.end()&&branch(it->opcode,edge.first)==edge.second,\n             \"V86 original asynchronous IOS call edge missing\");\n   }"

def derive(source):
    source=previous(source)
    if source.count(OLD)!=1 or NEW in source:
        raise ValueError("V86 generator boundary anchor differs")
    return source.replace(OLD,NEW,1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as out:
        out.write(result)

if __name__=="__main__":
    main()
