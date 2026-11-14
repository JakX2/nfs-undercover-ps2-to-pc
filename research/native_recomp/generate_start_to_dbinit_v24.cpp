// Source-only bounded original Wii __start -> DBInit -> synthetic OSInit generator.
// All owner DOL bytes and generated game C++ remain private.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t START=0x8000403c,INIT=0x80004238,REGS=0x800041a8,HW=0x800042e0;
constexpr uint32_t DBINIT=0x804e5020,OSINIT=0x80520670,DBPRINTF=0x804e50b8;
constexpr uint32_t STOP=0x80004160, PS=0x80520fb4, FPR=0x8051fbb0, CACHE=0x80522540;
constexpr uint32_t ERR=0x805230b8;
void require(bool v,const std::string& msg){if(!v)throw std::runtime_error(msg);}
uint32_t be32(const uint8_t* data){return (uint32_t(data[0])<<24)|(uint32_t(data[1])<<16)|(uint32_t(data[2])<<8)|data[3];}
uint32_t branch(uint32_t ins,uint32_t pc){
 require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");
 uint32_t imm=ins&0x03fffffc;
 if(imm&0x02000000)imm|=0xfc000000;
 return pc+imm;
}
void verify_file(const std::filesystem::path& path){
 std::ifstream in(path,std::ios::binary|std::ios::ate);
 require(bool(in),"failed opening private test DOL");
 const auto bytes=in.tellg();
 require(bytes>=0x100 && bytes<=128*1024*1024,"malformed DOL file size");
 in.seekg(0);std::array<uint8_t,256> header{};
 require(bool(in.read(reinterpret_cast<char*>(header.data()),header.size())),"short DOL header");
 std::vector<std::pair<uint64_t,uint64_t>> file_regions,guest_regions;
 unsigned sections=0;
 for(unsigned data=0;data<2;++data){
  for(unsigned i=0;i<(data?11u:7u);++i){
   uint32_t off=be32(header.data()+(data?0x1c:0)+4*i);
   uint32_t addr=be32(header.data()+(data?0x64:0x48)+4*i);
   uint32_t n=be32(header.data()+(data?0xac:0x90)+4*i);
   if(off==0 && n==0)continue;
   require(off>=256 && n && ((off|addr)&3u)==0,"invalid DOL section offset/alignment");
   require(uint64_t(off)+n<=static_cast<uint64_t>(bytes),"DOL section exceeds file");
   uint64_t end=uint64_t(addr)+n;
   require((addr>=0x80000000u && end<=0x81800000ull)||
           (addr>=0x90000000u && end<=0x94000000ull),"DOL section outside guest RAM");
   for(const auto& [start,stop]:file_regions)
    require(off>=stop || uint64_t(off)+n<=start,"overlapping DOL file sections");
   for(const auto& [start,stop]:guest_regions)
    require(addr>=stop || end<=start,"overlapping DOL guest sections");
   file_regions.emplace_back(off,uint64_t(off)+n);
   guest_regions.emplace_back(addr,end);
   ++sections;
  }
 }
 require(sections==8,"V24 expects seven code sections and one table");
 require(be32(header.data()+0xe0)==START,"wrong DOL entry");
}
}
int main(int argc,char** argv)try{
 require(argc==4,"Usage: generator PRIVATE.DOL EMPTY_DIR owner|synthetic");
 const std::string mode=argv[3];
 require(mode=="owner"||mode=="synthetic","unknown V24 mode");
 const bool owner=mode=="owner";
 const std::filesystem::path output=argv[2];
 require(std::filesystem::is_directory(output)&&std::filesystem::is_empty(output),
         "output directory must exist and be empty");
 verify_file(argv[1]);
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1]),"private test image load failed");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({FPR,CACHE});
 const auto& funcs=analyzer.get_functions();
 require(funcs.size()==(owner?26u:21u),"unexpected analyzed function count: "+std::to_string(funcs.size()));
 for(uint32_t pc:{START,REGS,HW,INIT,PS,FPR,CACHE,DBINIT,DBPRINTF,OSINIT,ERR})
  require(funcs.count(pc)==1,"missing expected PPC function");
 const auto& start=funcs.at(START).instructions;
 require(start.size()==(owner?74u:10u),"startup entry function size changed");
 require(branch(start.at(0).opcode,START)==REGS && branch(start.at(1).opcode,START+4)==HW,
         "original entry register/hardware calls changed");
 require(branch(start.at(6).opcode,START+24)==INIT,"original third startup call changed");
 if(owner){
  require(start.at(7).opcode==0x38000000u,"expected original post-data LI zero");
  for(const auto& [at,target] : std::array<std::pair<uint32_t,uint32_t>,2>{{{0x80004158u,DBINIT},{0x8000415cu,OSINIT}}}){
   bool found=false;
   for(const auto& ins:start)if(ins.address==at){require(branch(ins.opcode,at)==target,"original DB/OS startup call target changed");found=true;}
   require(found,"original DB/OS startup call missing");
  }
  for(uint32_t pc:{0x800040c8u,0x800040dcu}){
   const auto idx=(pc-START)/4;
   require(start.at(idx).opcode==0x44000002u,"alternative boot branch must be test-only guarded");
  }
  require(start.back().address==STOP && start.back().opcode==0x4e800020u,
          "missing synthetic stop continuation BLR");
  const auto& db=funcs.at(DBINIT).instructions;
  require(db.size()==10 && db.back().opcode==0x4e800020u,"original DBInit incomplete");
  require(db.at(5).opcode>>26==36 && db.at(7).opcode>>26==36 && db.at(8).opcode>>26==36,
          "original DBInit guest stores changed");
 }else{
  const auto& db=funcs.at(DBINIT).instructions;
  require(db.size()==4 && db.back().opcode==0x4e800020u, "synthetic DBInit incomplete");
  require(db[0].opcode==0x3d208003u && db[1].opcode==0x394055aau &&
          db[2].opcode==0x91497000u, "synthetic DBInit body does not match test fixture");
  require(branch(start.at(7).opcode,0x80004058u)==DBINIT &&
          branch(start.at(8).opcode,0x8000405cu)==OSINIT,"synthetic DBInit/OSInit calls missing");
 }
 for(uint32_t stop:{OSINIT,DBPRINTF,ERR}){
  const auto& f=funcs.at(stop).instructions;
  require(f.size()==2 && f[0].opcode==0x44000002u &&f[1].opcode==0x4e800020u,
          "unimplemented service missing explicit synthetic boundary");
 }
 nwii::recomp::RecompilerConfig config;
 config.output_dir=output.string();config.split_output=false;
 nwii::recomp::Recompiler generator(analyzer,nullptr,config);
 auto files=generator.generate_cpp(START);
 require(files.size()==1 && files[0]=="output.cpp","unexpected output configuration");
 std::cout<<"PASS: V24 native startup dispatcher, mode="<<mode
          <<" functions="<<funcs.size()<<" original_DBInit="<<owner<<"\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V24 generator: "<<e.what()<<"\n";return 1;}
