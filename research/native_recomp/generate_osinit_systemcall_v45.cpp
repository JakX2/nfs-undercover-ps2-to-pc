// Original-free NWiiRecomp driver for an owner-private Wii syscall-vector test.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x805290C8u,SOURCE=0x805290A8u,COPY=0x80004338u;
constexpr uint32_t DC=0x80522320u,IC=0x80522378u,STOP=0x80004900u;
void require(bool good,const std::string& reason){if(!good)throw std::runtime_error(reason);}
uint32_t be32(const uint8_t*p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|uint32_t(p[3]);}
uint64_t fnv(const std::vector<uint8_t>&data,uint32_t offset,uint32_t count){
 require(uint64_t(offset)+count<=data.size(),"private source range truncated");
 uint64_t hash=0xcbf29ce484222325ULL;
 for(uint32_t i=0;i<count;++i)hash=(hash^data[offset+i])*0x100000001b3ULL;
 return hash;
}
uint32_t target(uint32_t opcode,uint32_t pc){
 require(opcode>>26==18&&(opcode&1),"expected original PowerPC bl");
 int32_t delta=static_cast<int32_t>(opcode&0x03fffffcu);
 if(delta&0x02000000)delta-=0x04000000;
 return (opcode&2)?uint32_t(delta):pc+uint32_t(delta);
}
void expect_call(const nwii::analyzer::Function&f,uint32_t site,uint32_t dest){
 for(const auto&ins:f.instructions)if(ins.address==site){
  require(target(ins.opcode,site)==dest,"original helper call target changed");return;
 }
 throw std::runtime_error("required guest callsite missing");
}
}
int main(int argc,char**argv)try{
 require(argc==3,"usage: generate_osinit_systemcall_v45 PRIVATE_DOL EMPTY_OUTPUT_DIR");
 const std::filesystem::path path=argv[1],out=argv[2];
 require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),
         "native output directory must already exist and be empty");
 std::ifstream in(path,std::ios::binary|std::ios::ate);
 require(bool(in),"missing private DOL");
 const auto size=in.tellg();
 require(size>=256&&size<1024*1024,"private DOL size invalid");
 std::vector<uint8_t> blob(static_cast<size_t>(size));
 in.seekg(0);
 require(bool(in.read(reinterpret_cast<char*>(blob.data()),blob.size())),"private DOL truncated");
 constexpr std::array<uint32_t,5> guests{SOURCE,COPY,DC,IC,STOP};
 constexpr std::array<uint32_t,5> lengths{0x80u,80u,44u,52u,8u};
 constexpr std::array<uint64_t,3> expected_helper_hash{
     0x48d07741ff0575b4ULL, 0x436c87cd24625ee1ULL,
     0x9200294d16054a27ULL};
 for(size_t i=0;i<18;++i){
  const bool text=i<7;const uint32_t j=text?i:static_cast<uint32_t>(i-7);
  const uint32_t off=be32(blob.data()+(text?0:0x1c)+4*j);
  const uint32_t addr=be32(blob.data()+(text?0x48:0x64)+4*j);
  const uint32_t len=be32(blob.data()+(text?0x90:0xac)+4*j);
  if(i>=5){require(off==0&&addr==0&&len==0,"unexpected extra private DOL segment");continue;}
  require(addr==guests[i]&&len==lengths[i]&&off>=256&&uint64_t(off)+len<=blob.size(),
          "private DOL section geometry invalid");
  if(i==0){
   require(fnv(blob,off,128u)==0x424cb62d2e681d62ULL,
           "original Wii system-call template/function mutated");
  } else if(i<4)require(fnv(blob,off,len)==expected_helper_hash[i-1],
                 "original Wii helper PPC bytes mutated");
  else require(be32(blob.data()+off)==0x44000002u&&
               be32(blob.data()+off+4)==0x4e800020u,
               "explicit synthetic end-of-test syscall changed");
  for(size_t prev=0;prev<i;++prev){
   const uint32_t at=be32(blob.data()+4*prev);
   const uint32_t n=be32(blob.data()+0x90+4*prev);
   require(uint64_t(off)>=uint64_t(at)+n || uint64_t(at)>=uint64_t(off)+len,
           "private DOL sections overlap in file");
   const uint32_t a=be32(blob.data()+0x48+4*prev);
   require(uint64_t(addr)>=uint64_t(a)+n||uint64_t(a)>=uint64_t(addr)+len,
           "private DOL sections overlap in guest memory");
  }
 }
 require(be32(blob.data()+0xe0)==ENTRY,"private DOL entry point changed");
 nwii::loader::Executable exe;
 require(exe.load_dol(path.string())&&exe.entry_point==ENTRY,"private DOL failed loader");
 nwii::analyzer::Analyzer a(exe);
 a.analyze({STOP});
 const auto& funcs=a.get_functions();
 require(funcs.size()==7,"unexpected analyzer function-root count");
 for(uint32_t address:{ENTRY,COPY,DC,IC,STOP})
  require(funcs.count(address)==1,"missing translated original helper or stop");
 const auto&body=funcs.at(ENTRY).instructions;
 require(body.size()==24&&body.front().opcode==0x9421fff0u&&
         body.back().opcode==0x4e800020u,"original system-call initializer incomplete");
 expect_call(funcs.at(ENTRY),ENTRY+0x2c,COPY);
 expect_call(funcs.at(ENTRY),ENTRY+0x38,DC);
 expect_call(funcs.at(ENTRY),ENTRY+0x48,IC);
 for(const auto&[pc,n]:std::array<std::pair<uint32_t,size_t>,3>{{{COPY,20},{DC,11},{IC,13}}}){
  const auto&f=funcs.at(pc).instructions;
  require(f.size()==n&&f.back().opcode==0x4e800020u,"cache or memcpy helper incomplete");
 }
 const auto&s=funcs.at(STOP).instructions;
 require(s.size()==2&&s[0].opcode==0x44000002u&&s[1].opcode==0x4e800020u,
         "invalid private termination boundary");
 nwii::recomp::RecompilerConfig cfg;
 cfg.output_dir=out.string();cfg.split_output=false;
 nwii::recomp::Recompiler compiler(a,nullptr,cfg);
 const auto files=compiler.generate_cpp(ENTRY);
 require(files.size()==1&&files[0]=="output.cpp","unexpected native C++ output shape");
 std::cout<<"PASS: V45 original Wii system-call initializer and cache functions emitted (roots="
          <<funcs.size()<<")\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V45 generator rejected private image: "<<e.what()<<'\n';return 1;}
