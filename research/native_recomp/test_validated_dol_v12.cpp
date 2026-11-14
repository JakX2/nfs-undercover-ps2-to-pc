// Original-free synthetic DOL regression for actual NWiiRuntime loader.
#include "loader/validated_dol_v12.h"
#include "loader/loader.h"
#include <algorithm>
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
using nwii::loader::parse_validated_dol_v12;
using nwii::loader::ValidatedDolV12;
using nwii::loader::Executable;
static unsigned checks=0;
static void check(bool good, const std::string& why) {
    if(!good) throw std::runtime_error(why);
    ++checks;
}
static void set32(std::vector<uint8_t>& v, size_t o, uint32_t x) {
    v.at(o)=static_cast<uint8_t>(x>>24);
    v.at(o+1)=static_cast<uint8_t>(x>>16);
    v.at(o+2)=static_cast<uint8_t>(x>>8);
    v.at(o+3)=static_cast<uint8_t>(x);
}
static std::vector<uint8_t> fixture() {
    std::vector<uint8_t> b(0x118,0);
    set32(b,0x00,0x100);set32(b,0x48,0x80004000);set32(b,0x90,16);
    set32(b,0x1c,0x110);set32(b,0x64,0x80006000);set32(b,0xac,8);
    set32(b,0xd8,0x80005ff0);set32(b,0xdc,0x20); // valid BSS/data overlap
    set32(b,0xe0,0x80004000);
    for(unsigned i=0;i<16;i++)b[0x100+i]=static_cast<uint8_t>(i+1);
    for(unsigned i=0;i<8;i++)b[0x110+i]=static_cast<uint8_t>(0xa0+i);
    return b;
}
static void write(const fs::path& p, const std::vector<uint8_t>& b) {
    std::ofstream out(p,std::ios::binary|std::ios::trunc);
    if(!out.write(reinterpret_cast<const char*>(b.data()),b.size()))
        throw std::runtime_error("write fixture failed");
}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    auto source=fixture();
    ValidatedDolV12 parsed;
    std::string error;
    check(parse_validated_dol_v12(source,parsed,error),"valid DOL fixture must parse: "+error);
    check(parsed.entry_point==0x80004000,"fixture entry");
    check(parsed.sections.size()==3,"text, initialized data, BSS");
    check(parsed.sections[0].executable,"text section flag");
    check(!parsed.sections[1].executable&&!parsed.sections[1].is_bss,"data section flag");
    check(parsed.sections[2].is_bss,"BSS section flag");
    check(parsed.sections[2].guest_address==0x80005ff0 && parsed.sections[2].size==32,"BSS fields");
    check(parsed.sections[1].guest_address==0x80006000,"overlapping initialized data accepted");
    auto invalid=[&](std::vector<uint8_t> b,const char* why) {
        ValidatedDolV12 keep=parsed;
        std::string diagnostic;
        check(!parse_validated_dol_v12(b,keep,diagnostic),why);
        check(!diagnostic.empty(),std::string(why)+" must provide reason");
        check(keep.sections.size()==parsed.sections.size(),std::string(why)+" no partial output");
    };
    {auto b=source;b.resize(0xff);invalid(b,"truncated header");}
    {auto b=source;b.resize(0x117);invalid(b,"truncated file payload");}
    {auto b=source;set32(b,0x00,0);invalid(b,"empty text offset");}
    {auto b=source;set32(b,0x90,0);invalid(b,"empty text size");}
    {auto b=source;set32(b,0x90,0x100);invalid(b,"out-of-file text size");}
    {auto b=source;set32(b,0x00,0xff);invalid(b,"header pointer");}
    {auto b=source;set32(b,0x00,0x101);invalid(b,"misaligned file offset");}
    {auto b=source;set32(b,0x48,0x80004001);invalid(b,"unaligned guest address");}
    {auto b=source;set32(b,0x48,0x70004000);invalid(b,"guest address outside RAM");}
    {auto b=source;set32(b,0x48,0x817ffffc);invalid(b,"MEM1 boundary overrun");}
    {auto b=source;set32(b,0xe0,0x80004001);invalid(b,"entry alignment");}
    {auto b=source;set32(b,0xe0,0x80006000);invalid(b,"entry inside data not code");}
    {auto b=source;set32(b,0x1c,0x100);invalid(b,"overlapping file sections");}
    {auto b=source;set32(b,0x64,0x80004000);invalid(b,"overlapping guest sections");}
    {auto b=source;set32(b,0xd8,0x90000001);invalid(b,"unaligned BSS");}
    {auto b=source;set32(b,0xd8,0x817ffffc);invalid(b,"BSS boundary overflow");}
    {auto b=source;set32(b,0x00,0);set32(b,0x90,0);set32(b,0x1c,0);set32(b,0xac,0);invalid(b,"all sections absent");}
    const fs::path path=argv[1];
    write(path,source);
    Executable exe;
    check(exe.load_dol(path.string()),"actual NWiiRuntime loader accepts validated synthetic image");
    check(exe.entry_point==0x80004000,"actual loader entry point");
    check(exe.sections.size()==3,"actual loader section count");
    check(exe.sections[0].data.size()==16,"actual loader text bytes");
    check(exe.sections[0].data[0]==1&&exe.sections[0].data[15]==16,"actual loader text content");
    check(exe.sections[1].data[0]==0xa0&&exe.sections[1].data[7]==0xa7,"actual loader data content");
    check(exe.sections[2].data.empty(),"BSS not redundantly allocated");
    auto bad=source;bad.resize(0x117);write(path,bad);
    check(!exe.load_dol(path.string()),"actual NWiiRuntime rejects short section payload");
    check(exe.sections.size()==3,"failed load keeps prior sections atomically");
    check(exe.entry_point==0x80004000,"failed load keeps prior entry");
    fs::remove(path);
    std::cout<<"PASS: "<<checks<<" synthetic validated-DOL parser + actual loader assertions\n";
}
