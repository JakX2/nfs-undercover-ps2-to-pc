// Independent fail-closed native translation of owner-original Wii EXIInit polling prefix.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x804EF9BCu,STOP=0x804EFA14u;
void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
uint32_t word(const uint8_t *p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint64_t fnv(const uint8_t *p,size_t n){uint64_t h=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)h=(h^p[i])*0x100000001b3ULL;return h;}
}
int main(int argc,char**argv)try{
 need(argc==3,"usage: generator PRIVATE_EXI_DOL EMPTY_OUTPUT_DIR");
 const std::filesystem::path dir=argv[2];
 need(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"output must be existing empty directory");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);
 need(bool(f)&&f.tellg()==352,"private fixture size changed");
 std::vector<uint8_t>b(352);f.seekg(0);need(bool(f.read(reinterpret_cast<char*>(b.data()),b.size())),"truncated test image");
 for(int i=0;i<18;++i){
  bool text=i<7;int j=text?i:i-7;
  uint32_t o=word(b.data()+(text?0:0x1c)+j*4);
  uint32_t base=word(b.data()+(text?0x48:0x64)+j*4);
  uint32_t len=word(b.data()+(text?0x90:0xac)+j*4);
  if(i==0)need(o==0x100&&base==ENTRY&&len==0x60,"unexpected original EXI fixture geometry");
  else need(!o&&!base&&!len,"unrecognized DOL section");
 }
 need(word(b.data()+0xe0)==ENTRY&&word(b.data()+0x100+STOP-ENTRY)==0x44000002u&&word(b.data()+0x100+STOP-ENTRY+4)==0x4e800020u,"private original EXI stop changed");
 need(fnv(b.data()+0x100,0x60)==0x9e4c90a9d9b9c4f1ULL,"original/synthetic EXI PPC words mutated");
 nwii::loader::Executable exe;need(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"private EXI DOL load failed");
 nwii::analyzer::Analyzer a(exe);a.analyze({STOP});
 const auto& fs=a.get_functions();
 std::cerr<<"V65 analyzer entries: "<<fs.size()<<'\n';
 for(const auto&[pc,fn]:fs)std::cerr<<std::hex<<pc<<std::dec<<" instructions="<<fn.instructions.size()<<'\n';
 need(fs.count(ENTRY)==1&&fs.count(STOP)==1,"missing original EXI entry/test stop");
 need(fs.at(ENTRY).instructions.size()==24u,"incomplete EXI poll prefix");
 auto opcode=[&](uint32_t pc){for(const auto& ins:fs.at(ENTRY).instructions)if(ins.address==pc)return ins.opcode;throw std::runtime_error("EXI original opcode missing");};
 for(const uint32_t pc:{0x804EF9E8u,0x804EF9F8u,0x804EFA08u})need(opcode(pc)>>26==16u,"original EXI backedge missing");
 for(const uint32_t pc:{0x804EF9DCu,0x804EF9ECu,0x804EF9FCu})need(opcode(pc)>>26==32u,"original EXI MMIO read missing");
 nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=false;
 nwii::recomp::Recompiler rc(a,nullptr,cfg);auto result=rc.generate_cpp(ENTRY);
 need(result.size()==1&&result[0]=="output.cpp","no native EXI translation emitted");
 std::cout<<"PASS: V65 owner-original EXI MMIO loop native translation"<<'\n';
 return 0;
}catch(const std::exception&e){std::cerr<<"V65 generator: "<<e.what()<<'\n';return 1;}
