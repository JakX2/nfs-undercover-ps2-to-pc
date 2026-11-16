// Verify private game-derived inputs before emitting NWiiRecomp native C++.
// No proprietary PowerPC instruction words are embedded in this source.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
void require(bool cond,const char*msg){if(!cond)throw std::runtime_error(msg);}
uint32_t be(const uint8_t*p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint64_t fnv(const uint8_t*p,size_t n){uint64_t h=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)h=(h^p[i])*0x100000001b3ULL;return h;}
constexpr uint32_t MASK=0x8052693cu,DIS=0x805265acu,REST=0x805265d4u,SET=0x805266e0u,STOP=0x90050000u;
constexpr std::array<uint32_t,5> bases{MASK,DIS,REST,SET,STOP};
constexpr std::array<uint32_t,5> lengths{0x80u,0x14u,0x24u,0x25cu,8u};
constexpr std::array<uint64_t,5> hashes{0x4a5301c69f3696a8ULL,0x048e9e3d231e7b0aULL,0x8c558aaea8697424ULL,0xbca68359fb2611b2ULL,0xbc3e71dcd1be5e75ULL};
}
int main(int argc,char**argv)try {
 require(argc==3,"usage: generator PRIVATE_DOL EMPTY_OUTPUT_DIR");
 const std::filesystem::path out=argv[2];require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"refuse nonempty output directory");
 std::ifstream in(argv[1],std::ios::ate|std::ios::binary);
 require(bool(in)&&in.tellg()==1052,"private DOL trailing data or size mismatch");
 std::vector<uint8_t>b(1052);in.seekg(0);require(bool(in.read(reinterpret_cast<char*>(b.data()),b.size())),"private DOL read failed");
 uint32_t offset=0x100;
 for(int i=0;i<18;++i){
  bool text=i<7;int k=text?i:i-7;
  uint32_t o=be(b.data()+(text?0:0x1c)+4*k);
  uint32_t base=be(b.data()+(text?0x48:0x64)+4*k);
  uint32_t size=be(b.data()+(text?0x90:0xac)+4*k);
  if(i<5){
   require(o==offset&&base==bases[i]&&size==lengths[i],"private DOL section geometry changed");
   require(fnv(b.data()+offset,size)==hashes[i],"original Wii PowerPC segment or synthetic test stop mutated");
   offset+=size;
  }else require(!o&&!base&&!size,"unexpected section in private DOL");
 }
 require(offset==b.size()&&be(b.data()+0xe0)==MASK,"private DOL entry or padding changed");
 nwii::loader::Executable exe;require(exe.load_dol(argv[1])&&exe.entry_point==MASK,"private Wii DOL failed to load");
 nwii::analyzer::Analyzer a(exe);a.analyze({STOP});
 auto& funcs=a.get_functions();
 std::cerr<<"V67 native analyzer entries="<<funcs.size()<<"\n";
 for(auto&[address,fn]:funcs)std::cerr<<std::hex<<address<<std::dec<<" instructions="<<fn.instructions.size()<<"\n";
 for(uint32_t pc:bases)require(funcs.count(pc)==1,"original function or synthetic return not recovered");
 require(funcs.at(MASK).instructions.size()==32,"incomplete original __OSMaskInterrupts");
 require(funcs.at(DIS).instructions.size()==5,"incomplete interrupt-disable helper");
 require(funcs.at(REST).instructions.size()==9,"incomplete restore-interrupts helper");
 require(funcs.at(SET).instructions.size()==151,"incomplete original SetInterruptMask");
 for(uint32_t pc:{MASK,DIS,REST,SET})require(funcs.at(pc).instructions.back().opcode==0x4e800020,"original return missing");
 require(funcs.at(STOP).instructions[0].opcode==0x44000002,"test-only stop not isolated");
 auto call=[&](uint32_t at,uint32_t target){
  for(auto&ins:funcs.at(MASK).instructions)if(ins.address==at){
    require((ins.opcode>>26)==18,"original call site is not a branch");
    uint32_t disp=ins.opcode&0x3fffffcu;int32_t relative=int32_t(disp<<6)>>6;
    require(uint32_t(at+relative)==target,"original call target changed");return;
  }throw std::runtime_error("original call site absent");
 };
 call(0x80526958u,DIS);call(0x80526988u,SET);call(0x80526998u,REST);
 nwii::recomp::RecompilerConfig cfg;cfg.output_dir=out.string();cfg.split_output=false;
 nwii::recomp::Recompiler repl(a,nullptr,cfg);auto emitted=repl.generate_cpp(MASK);
 require(emitted.size()==1&&emitted[0]=="output.cpp","unexpected native C++ output");
 std::cout<<"PASS: V67 original Wii mask, interrupt helpers and SetInterruptMask translated\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V67 generator: "<<e.what()<<'\n';return 1;}
