// Source-only original Wii alarm native generator; reads a private SHA-checked slice.
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
constexpr uint32_t ALARM=0x805210CCu,GET=0x80520EB0u,SET=0x80520E9Cu,
                   SHUTDOWN=0x80527B4Cu,STOP=0x80004900u;
void check(bool good,const char*reason){if(!good)throw std::runtime_error(reason);}
uint32_t be32(const uint8_t*p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|uint32_t(p[3]);}
uint64_t fnv(const uint8_t*p,size_t n){uint64_t h=0xcbf29ce484222325ULL;
 for(size_t i=0;i<n;++i)h=(h^p[i])*0x100000001b3ULL;return h;}
uint32_t target(uint32_t opcode,uint32_t pc){
 check((opcode>>26)==18&&(opcode&1)==1,"BL opcode changed");
 int32_t delta=static_cast<int32_t>(opcode&0x03fffffcu);
 if(delta&0x02000000)delta-=0x04000000;
 return (opcode&2)?uint32_t(delta):pc+uint32_t(delta);
}
void expect(const nwii::analyzer::Function&f,uint32_t site,uint32_t dest){
 for(const auto&ins:f.instructions)if(ins.address==site){
  check(target(ins.opcode,site)==dest,"callgraph changed");return;}
 throw std::runtime_error("original alarm callsite missing");
}
}
int main(int argc,char**argv)try{
 check(argc==3,"usage: generate_alarm_v47 PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path out=argv[2];
 check(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"private C++ output dir must be empty");
 std::ifstream in(argv[1],std::ios::binary|std::ios::ate);check(bool(in),"private test DOL missing");
 const auto size=in.tellg();check(size>=256&&size<4096,"private alarm DOL size changed");
 std::vector<uint8_t> blob(static_cast<size_t>(size));in.seekg(0);
 check(bool(in.read(reinterpret_cast<char*>(blob.data()),blob.size())),"test DOL truncated");
 constexpr std::array<uint32_t,4> addresses{ALARM,SET,SHUTDOWN,STOP};
 constexpr std::array<uint32_t,4> lengths{0x58u,0x24u,0x88u,8u};
 constexpr std::array<uint64_t,4> hashes{0xdb75bee478a21f20ULL,0x39c53f9ff1ea2a9aULL,0xe952b00f18c233d6ULL,0xbc3e71dcd1be5e75ULL}; // Replaced after verifying owner's private DOL
 uint32_t expected_file_offset=256u;
 for(size_t i=0;i<18;++i){
  const uint32_t j=static_cast<uint32_t>(i<7?i:i-7);
  const uint32_t off=be32(blob.data()+(i<7?0:0x1c)+4*j);
  const uint32_t address=be32(blob.data()+(i<7?0x48:0x64)+4*j);
  const uint32_t len=be32(blob.data()+(i<7?0x90:0xac)+4*j);
  if(i>=4){check(off==0&&address==0&&len==0,"unexpected DOL section");continue;}
  check(address==addresses[i]&&len==lengths[i]&&off==expected_file_offset&&uint64_t(off)+len<=blob.size(),"DOL geometry mismatch");
  expected_file_offset+=len;
  check(fnv(blob.data()+off,len)==hashes[i],"original Wii alarm instructions or synthetic stop mutated");
 }
 check(blob.size()==expected_file_offset,"private alarm DOL has unexpected trailing bytes");
 check(be32(blob.data()+0xe0)==ALARM,"incorrect original alarm entry");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==ALARM,"owner-private DOL load rejected");
 nwii::analyzer::Analyzer a(exe);a.analyze({STOP});
 const auto&fs=a.get_functions();
 check(fs.size()==5,"unanticipated analyzer function roots");
 for(uint32_t pc:{ALARM,GET,SET,SHUTDOWN,STOP})
  check(fs.count(pc)==1,"missing original alarm service or synthetic stop");
 expect(fs.at(ALARM),ALARM+0x10u,GET);
 expect(fs.at(ALARM),ALARM+0x38u,SET);
 expect(fs.at(ALARM),ALARM+0x44u,SHUTDOWN);
 check(fs.at(ALARM).instructions.size()==22,"alarm source incomplete");
 check(fs.at(GET).instructions.size()==4&&fs.at(SET).instructions.size()==5,
  "original exception getter/setter incomplete");
 check(fs.at(SHUTDOWN).instructions.size()==34,"original shutdown function incomplete");
 check(fs.at(STOP).instructions.size()==2&&fs.at(STOP).instructions[0].opcode==0x44000002u,
  "test stop changed");
 nwii::recomp::RecompilerConfig cfg;cfg.output_dir=out.string();cfg.split_output=false;
 nwii::recomp::Recompiler recomp(a,nullptr,cfg);
 const auto outputs=recomp.generate_cpp(ALARM);
 check(outputs.size()==1&&outputs[0]=="output.cpp","unexpected generated C++ files");
 std::cout<<"PASS: V47 original Wii alarm, exception getter/setter, shutdown registration emitted, roots="<<fs.size()<<'\n';
 return 0;
}catch(const std::exception&e){std::cerr<<"V47 generator: "<<e.what()<<'\n';return 1;}
