// Independently written fail-closed test generator for original Wii error-handler code.
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
constexpr uint32_t ERR=0x805230B8u, END=0x80523340u;
void require(bool b,const char*s){if(!b)throw std::runtime_error(s);}
uint32_t be32(const uint8_t *p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint64_t fnv(const uint8_t *p,size_t n){uint64_t v=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)v=(v^p[i])*0x100000001b3ULL;return v;}
uint32_t target(uint32_t w,uint32_t pc){require(w>>26==18&&(w&1),"original bl opcode absent");int32_t off=int32_t(w&0x03fffffcu);if(off&0x02000000)off-=0x04000000;return (w&2)?uint32_t(off):pc+uint32_t(off);}
void check_call(const nwii::analyzer::Function &f,uint32_t pc,uint32_t dst){for(const auto&i:f.instructions)if(i.address==pc){require(target(i.opcode,pc)==dst,"original Wii callgraph differs");return;}throw std::runtime_error("original callsite missing");}
}
int main(int argc,char **argv)try{
 require(argc==3,"usage: generate_errorhandler PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path out(argv[2]);require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"output must exist and be empty");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);require(bool(f),"missing private fixture");
 auto len=f.tellg();require(len==1192,"V63 private fixture length changed");
 std::vector<uint8_t> bytes(static_cast<size_t>(len));f.seekg(0);require(bool(f.read(reinterpret_cast<char*>(bytes.data()),bytes.size())),"truncated private Wii fixture");
 constexpr std::array<uint32_t,3> bases{ERR,0x805265ACu,0x804B7910u};
 constexpr std::array<uint32_t,3> sizes{0x290u,0x4cu,0xccu};
 constexpr std::array<uint32_t,3> offsets{0x100u,0x390u,0x3dcu};
 constexpr std::array<uint64_t,3> hashes{0x6e745ac6cb12496aULL,0x6c992ef9c6d2ce32ULL,0x13b050f244775ef4ULL};
 for(unsigned i=0;i<18;++i){
   const unsigned index=i<7?i:i-7;
   const bool is_text=i<7;
   uint32_t off=be32(bytes.data()+(is_text?0:0x1c)+4*index);
   uint32_t base=be32(bytes.data()+(is_text?0x48:0x64)+4*index);
   uint32_t sz=be32(bytes.data()+(is_text?0x90:0xac)+4*index);
   if(i<3){require(off==offsets[i]&&base==bases[i]&&sz==sizes[i],"section geometry differs");require(fnv(bytes.data()+off,sz)==hashes[i],"original PPC or synthetic stop changed");}
   else require(off==0&&base==0&&sz==0,"unexpected private test section");
 }
 require(be32(bytes.data()+0xe0)==ERR&&be32(bytes.data()+0x100+END-ERR)==0x44000002u,"original entry or explicit terminal differs");
 nwii::loader::Executable exe;require(exe.load_dol(argv[1])&&exe.entry_point==ERR,"private Wii DOL loader rejected fixture");
 nwii::analyzer::Analyzer a(exe);a.analyze({END});
 const auto&fs=a.get_functions();
 std::cerr<<"V63 analyzer roots="<<fs.size()<<"\n";
 for(auto&[pc,fn]:fs)std::cerr<<std::hex<<pc<<std::dec<<" ins="<<fn.instructions.size()<<"\n";
 for(uint32_t pc:{ERR,END,0x805265ACu,0x805265D4u,0x804B7910u,0x804B7918u})require(fs.count(pc)==1,"missing original helper or synthetic terminal");
 require(fs.at(ERR).instructions.size()==0x288u/4u,"full original OSSetErrorHandler body missing");
 require(fs.at(ERR).instructions.back().opcode==0x4e800020u,"original handler return differs");
 check_call(fs.at(ERR),0x805230DCu,0x805265ACu);
 check_call(fs.at(ERR),0x80523318u,0x805265D4u);
 require(fs.at(0x805265ACu).instructions.size()==5u,"original interrupt disable incomplete");
 require(fs.at(0x805265D4u).instructions.size()==9u,"original interrupt restore incomplete");
 nwii::recomp::RecompilerConfig c;c.output_dir=out.string();c.split_output=false;
 nwii::recomp::Recompiler rc(a,nullptr,c);auto paths=rc.generate_cpp(ERR);
 require(paths.size()==1&&paths[0]=="output.cpp","unexpected native recompiler output");
 std::cout<<"PASS: V63 complete original Wii OSSetErrorHandler translated to native C++\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V63 native generator rejected: "<<e.what()<<"\n";return 1;}
