// Original-free, SHA-pinned native generation for one complete Wii SetInterruptMask helper.
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
constexpr uint32_t ENTRY=0x805266E0u, STOP=0x8052693Cu;
void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
uint32_t be32(const uint8_t*p){return uint32_t(p[0])<<24 | uint32_t(p[1])<<16 | uint32_t(p[2])<<8 | p[3];}
uint64_t fnv(const uint8_t*p,size_t n){uint64_t h=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)h=(h^p[i])*0x100000001b3ULL;return h;}
}
int main(int argc,char**argv)try{
 need(argc==3,"usage: generator PRIVATE_DOL EMPTY_OUTPUT_DIRECTORY");
 const std::filesystem::path dir=argv[2];
 need(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"output must be an empty existing directory");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);need(bool(f),"private DOL missing");
 const auto sz=f.tellg();need(sz==868,"private bounded DOL length changed");
 std::vector<uint8_t> data(static_cast<size_t>(sz)); f.seekg(0);
 need(bool(f.read(reinterpret_cast<char*>(data.data()),data.size())),"truncated private DOL");
 for(unsigned i=0;i<18;++i){
   const bool text=i<7;unsigned idx=text?i:i-7;
   uint32_t off=be32(data.data()+(text?0:0x1c)+idx*4);
   uint32_t addr=be32(data.data()+(text?0x48:0x64)+idx*4);
   uint32_t len=be32(data.data()+(text?0x90:0xac)+idx*4);
   if(i==0){need(off==0x100&&addr==ENTRY&&len==0x264,"private original text geometry changed");}
   else need(!off&&!addr&&!len,"unexpected extra private DOL section");
 }
 need(be32(data.data()+0xe0)==ENTRY,"unexpected original entrypoint");
 need(fnv(data.data()+0x100,0x264)==0xb5b7c21e7ca637beULL,"SHA-pinned private original PPC or test-stop opcode changed");
 need(be32(data.data()+0x100+STOP-ENTRY)==0x44000002u,"synthetic test stop changed");
 nwii::loader::Executable exe;need(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"cannot load original Wii private DOL");
 nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({STOP});
 const auto& fs=analyzer.get_functions();
 std::cerr<<"V54 analyzer roots="<<fs.size()<<"\n";
 for(const auto&[pc,fn]:fs)std::cerr<<std::hex<<pc<<std::dec<<" "<<fn.instructions.size()<<" instructions\n";
 need(fs.count(ENTRY)==1&&fs.count(STOP)==1,"missing original SetInterruptMask or test stop");
 // Every real instruction is original PPC; the 2 post-function instructions
 // are the sole test-only boundary and are not part of the original function.
 need(fs.at(ENTRY).instructions.size()>=100,"incomplete original multi-branch function");
 nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=false;
 nwii::recomp::Recompiler recompiler(analyzer,nullptr,cfg);
 auto paths=recompiler.generate_cpp(ENTRY);
 need(paths.size()==1&&paths[0]=="output.cpp","unexpected generated native output path");
 std::cout<<"PASS: V54 original full SetInterruptMask PPC emitted through NWiiRecomp\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V54 generator error: "<<e.what()<<'\n';return 1;}
