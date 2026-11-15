// Original-free generator for the authentic Wii interrupt mask loop and helpers.
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
constexpr uint32_t IRQ=0x8052661cu,STOP=0x805266acu;
void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
uint32_t be32(const uint8_t*p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint64_t fnv(const uint8_t*p,size_t n){uint64_t h=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)h=(h^p[i])*0x100000001b3ULL;return h;}
uint32_t bltarget(uint32_t op,uint32_t pc){need((op>>26)==18&&(op&1)==1,"expected original bl");int32_t disp=int32_t(op&0x03fffffcu);if(disp&0x02000000)disp-=0x04000000;return (op&2)?uint32_t(disp):pc+uint32_t(disp);}
void checkbl(const nwii::analyzer::Function&f,uint32_t pc,uint32_t destination){
 for(const auto&ins:f.instructions)if(ins.address==pc){need(bltarget(ins.opcode,pc)==destination,"original Wii callgraph differs");return;}
 throw std::runtime_error("required original PowerPC callsite not analyzed");
}
}
int main(int argc,char**argv)try{
 need(argc==3,"usage: generator PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path dir=argv[2];need(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"output must be a new empty directory");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);need(bool(f),"private DOL missing");
 const auto size=f.tellg();need(size==1260,"unexpected private image length");
 std::vector<uint8_t> data(static_cast<size_t>(size));f.seekg(0);
 need(bool(f.read(reinterpret_cast<char*>(data.data()),data.size())),"truncated private original DOL");
 constexpr std::array<uint32_t,4> addresses{0x805265acu,IRQ,0x805266e0u,0x80004388u};
 constexpr std::array<uint32_t,4> lengths{0x14u,0x98u,0x25cu,0xe4u};
 constexpr std::array<uint64_t,4> hashes{0x048e9e3d231e7b0aULL,0x2e67bbd2464e682bULL,0xbca68359fb2611b2ULL,0x473baf21744af378ULL};
 for(unsigned i=0;i<18;++i){bool text=i<7;unsigned idx=text?i:i-7;
   uint32_t off=be32(data.data()+(text?0:0x1c)+4*idx);
   uint32_t addr=be32(data.data()+(text?0x48:0x64)+4*idx);
   uint32_t n=be32(data.data()+(text?0x90:0xac)+4*idx);
   if(i>=4){need(!off&&!addr&&!n,"unexpected private DOL section");continue;}
   need(addr==addresses[i]&&n==lengths[i]&&off>=0x100u&&uint64_t(off)+n<=data.size(),"unexpected original/synthetic DOL geometry");
   need(fnv(data.data()+off,n)==hashes[i],"SHA-pinned private original PPC differs");
 }
 need(be32(data.data()+0xe0)==IRQ,"original interrupt entry changed");
 nwii::loader::Executable exe;need(exe.load_dol(argv[1])&&exe.entry_point==IRQ,"invalid original Wii private fixture");
 nwii::analyzer::Analyzer a(exe);a.analyze({STOP});const auto& funcs=a.get_functions();
 need(funcs.size()==6,"unexpected analyzer guest roots for original interrupt loop");
 std::cerr<<"V55 analyzer roots="<<funcs.size()<<"\n";
 for(const auto&[pc,fn]:funcs)std::cerr<<std::hex<<pc<<std::dec<<" "<<fn.instructions.size()<<" ins\n";
 for(uint32_t pc:{IRQ,STOP,0x805265acu,0x805266e0u,0x80004388u,0x8000443cu})
  need(funcs.count(pc)==1,"original interrupt initializer dependency missing");
 checkbl(funcs.at(IRQ),0x80526648u,0x8000443cu);
 checkbl(funcs.at(IRQ),0x80526674u,0x805265acu);
 checkbl(funcs.at(IRQ),0x805266a0u,0x805266e0u);
 checkbl(funcs.at(0x8000443cu),0x80004450u,0x80004388u);
 need(funcs.at(0x805266e0u).instructions.size()==151,"complete original SetInterruptMask not analyzed");
 need(funcs.at(IRQ).instructions.size()==38u,"original IRQ loop prefix must include all branch instructions and stop");
 nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=false;
 nwii::recomp::Recompiler recompiler(a,nullptr,cfg);
 auto files=recompiler.generate_cpp(IRQ);
 need(files.size()==1&&files[0]=="output.cpp","wrong generated C++ output");
 std::cout<<"PASS: V55 original interrupt initializer loop and full SetInterruptMask native C++ generated\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V55 generator: "<<e.what()<<'\n';return 1;}
