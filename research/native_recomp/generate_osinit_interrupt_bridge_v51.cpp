// Bounded original-free generator for original Wii OSInit/exception/syscall chain.
// Original PowerPC code is only loaded from a SHA-pinned owner-private test DOL.
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
constexpr uint32_t OSINIT=0x80520670u,SYSCALL=0x805290C8u;
constexpr uint32_t SOURCE=0x805290A8u,RESTGPR=0x80545134u;
constexpr uint32_t DBPRINTF=0x804E50B8u,STOP=0x8052664Cu;
constexpr uint32_t EXCEPTION=0x80520BF4u,COPY=0x80004338u;
constexpr uint32_t MODULE=0x80526D30u;
constexpr uint32_t INTERRUPT=0x8052661Cu, IRQ_STOP=0x8052664Cu, MEMSET=0x8000443Cu, FILL=0x80004388u;
constexpr uint32_t ALARM=0x805210CCu,GET=0x80520EB0u,SET=0x80520E9Cu,SHUTDOWN=0x80527B4Cu;
constexpr uint32_t DC=0x80522320u,IC=0x80522378u;
void need(bool value,const char*why){if(!value)throw std::runtime_error(why);}
uint32_t be32(const uint8_t* p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|uint32_t(p[3]);}
uint64_t fnv(const uint8_t* ptr,uint32_t n){uint64_t h=0xcbf29ce484222325ULL;for(uint32_t i=0;i<n;++i)h=(h^ptr[i])*0x100000001b3ULL;return h;}
uint32_t target(uint32_t op,uint32_t pc){
 need(op>>26==18&&(op&1),"expected original PowerPC bl");
 int32_t off=static_cast<int32_t>(op&0x03fffffcu);if(off&0x02000000)off-=0x04000000;
 return (op&2)?uint32_t(off):pc+uint32_t(off);
}
void expect(const nwii::analyzer::Function& f,uint32_t pc,uint32_t destination){
 for(const auto& ins:f.instructions)if(ins.address==pc){
  need(target(ins.opcode,pc)==destination,"original PPC callgraph mismatch");return;
 }
 throw std::runtime_error("missing original guest callsite");
}
}
int main(int argc,char**argv)try{
 need(argc==3,"usage: generator PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path out=argv[2];
 need(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"private output must be empty existing directory");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);
 need(bool(f),"missing private Wii image");
 const auto sz=f.tellg();need(sz>=256&&sz<1024*1024,"private DOL bounds changed");
 std::vector<uint8_t> data(static_cast<size_t>(sz));f.seekg(0);
 need(bool(f.read(reinterpret_cast<char*>(data.data()),data.size())),"private DOL truncated");
 constexpr std::array<uint32_t,8> guests{OSINIT,0x805265ACu,0x805450E8u,COPY,0x804B7920u,0x804E50A0u,0u,0x90050000u};
 constexpr std::array<uint32_t,8> lengths{0x34d0u,0x48ecu,0x80u,0x134u,0x160u,0x20u,0u,0x98u};
 constexpr std::array<uint64_t,8> hashes{
  0x2f915daa7cf37f65ULL,0x24288449fa16bdacULL,0x45313cdfb207c7d5ULL,
  0x9d2150ddab890eb5ULL,0x055c68f82fff5ffbULL,0x8becdc350b44b3f5ULL,
  0ULL,0x2578204771b7eb49ULL};
 for(size_t i=0;i<18;++i){
  const bool text=i<7;
  const size_t ind=text?i:i-7;
  const uint32_t offset=be32(data.data()+(text?0:0x1c)+ind*4);
  const uint32_t address=be32(data.data()+(text?0x48:0x64)+ind*4);
  const uint32_t length=be32(data.data()+(text?0x90:0xac)+ind*4);
  if(i>=8||i==6){
   need(offset==0&&address==0&&length==0,"unexpected DOL segment");continue;
  }
  need(address==guests[i]&&length==lengths[i]&&offset>=256&&uint64_t(offset)+length<=data.size(),
       "private test image section geometry changed");
  need(fnv(data.data()+offset,length)==hashes[i],"private original/synthetic source hash mismatch");
 }
 need(be32(data.data()+0xe0)==OSINIT,"unexpected original OSInit entry");
 nwii::loader::Executable exe;
 need(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"could not load private original DOL");
 nwii::analyzer::Analyzer a(exe);
 a.analyze({0x80520BDCu});
 const auto&fs=a.get_functions();
 if(fs.size()!=48){
  std::cerr << "V51 analyzed guest roots=" << fs.size() << " (expect 48)\n";
  for(const auto& [address, fn]:fs)std::cerr<<std::hex<<address<<std::dec<<" ins="<<fn.instructions.size()<<"\n";
  throw std::runtime_error("unexpected native analyzer roots");
 }
 for(uint32_t pc:{OSINIT,SYSCALL,RESTGPR,DBPRINTF,EXCEPTION,COPY,DC,IC,ALARM,GET,SET,SHUTDOWN,MODULE,INTERRUPT,MEMSET,FILL})
  need(fs.count(pc)==1,"missing original Wii integration function");
 expect(fs.at(OSINIT),0x805208ACu,SYSCALL);
 expect(fs.at(OSINIT),0x805208B0u,ALARM);
 expect(fs.at(OSINIT),0x805208B4u,MODULE);
 expect(fs.at(OSINIT),0x805208B8u,INTERRUPT);
 expect(fs.at(INTERRUPT),0x80526648u,MEMSET);
 expect(fs.at(MEMSET),0x80004450u,FILL);
 need(fs.at(INTERRUPT).instructions.size()==14u,"incomplete original interrupt prefix");
 need(fs.at(INTERRUPT).instructions[12].opcode==0x44000002u,"wrong interrupt stop instruction");
 need(fs.at(MEMSET).instructions.size()==12u&&fs.at(FILL).instructions.size()==45u,
      "incomplete authentic Wii memset/fill helpers");
 expect(fs.at(ALARM),ALARM+0x10u,GET);
 expect(fs.at(ALARM),ALARM+0x38u,SET);
 expect(fs.at(ALARM),ALARM+0x44u,SHUTDOWN);
 expect(fs.at(EXCEPTION),0x80520E58u,DBPRINTF);
 expect(fs.at(EXCEPTION),0x80520E60u,RESTGPR);
 expect(fs.at(SYSCALL),SYSCALL+0x2cu,COPY);
 expect(fs.at(SYSCALL),SYSCALL+0x38u,DC);
 expect(fs.at(SYSCALL),SYSCALL+0x48u,IC);
 need(fs.at(SYSCALL).instructions.size()==24,"full original syscall body missing");
 need(fs.at(ALARM).instructions.size()==22,"original alarm body incomplete");
 need(fs.at(MODULE).instructions.size()==6,"original OS module initializer incomplete");
 need(fs.at(MODULE).instructions.back().opcode==0x4e800020u,"module initializer return changed");
 need(fs.at(GET).instructions.size()==4&&fs.at(SET).instructions.size()==5,
      "original exception handler accessors incomplete");
 need(fs.at(SHUTDOWN).instructions.size()==34,"original shutdown registration incomplete");
 need(fs.at(RESTGPR).instructions.size()==13,"original _restgpr_20 thunk incomplete");
 need(fs.at(DBPRINTF).instructions.size()==2&&fs.at(DBPRINTF).instructions[0].opcode==0x44000002u,
      "DBPrintf synthetic callback changed");
 nwii::recomp::RecompilerConfig c;c.output_dir=out.string();c.split_output=false;
 nwii::recomp::Recompiler recomp(a,nullptr,c);
 auto outputs=recomp.generate_cpp(OSINIT);
 need(outputs.size()==1&&outputs[0]=="output.cpp","wrong generated C++ output");
 std::cout<<"PASS: V51 original Wii OSInit through interrupt memset prefix integrated, roots="<<fs.size()<<'\n';
 return 0;
}catch(const std::exception&e){std::cerr<<"V51 generator: "<<e.what()<<'\n';return 1;}
