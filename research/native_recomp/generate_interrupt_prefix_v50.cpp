// Owner-private original Wii interrupt initialization native-code generator.
// This independently written source never includes any original PPC code bytes.
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
constexpr uint32_t ENTRY=0x8052661Cu,STOP=0x8052664Cu;
constexpr uint32_t FILL=0x80004388u,MEMSET=0x8000443Cu;
void check(bool ok,const char* error){if(!ok)throw std::runtime_error(error);}
uint32_t big32(const uint8_t*p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint64_t fnv(const uint8_t*p,size_t n){uint64_t x=0xcbf29ce484222325ULL;for(size_t i=0;i<n;++i)x=(x^p[i])*0x100000001b3ULL;return x;}
uint32_t call(uint32_t word,uint32_t pc){
 check((word>>26)==18&&(word&1)==1,"expected authentic BL instruction");
 int32_t delta=int32_t(word&0x03fffffcu);if(delta&0x02000000)delta-=0x04000000;
 return (word&2)?uint32_t(delta):pc+uint32_t(delta);
}
void expect(const nwii::analyzer::Function& f,uint32_t pc,uint32_t dest){
 for(const auto&ins:f.instructions)if(ins.address==pc){check(call(ins.opcode,pc)==dest,"PPC callgraph changed");return;}
 throw std::runtime_error("required original callsite not analyzed");
}
}
int main(int argc,char**argv)try{
 check(argc==3,"usage: generator PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path dir=argv[2];
 check(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"private output dir must be empty");
 std::ifstream f(argv[1],std::ios::binary|std::ios::ate);
 check(bool(f),"cannot open private bounded DOL");
 auto count=f.tellg();check(count>0&&count<4096,"unexpected private image length");
 std::vector<uint8_t> file(static_cast<size_t>(count));f.seekg(0);
 check(bool(f.read(reinterpret_cast<char*>(file.data()),file.size())),"truncated private DOL");
 constexpr uint32_t addr[2]={ENTRY,FILL};
 constexpr uint32_t length[2]={0x38u,0xE4u};
 constexpr uint64_t hash[2]={0x878efa1e209b57ebULL,0x473baf21744af378ULL};
 for(unsigned i=0;i<18;++i){
   const bool is_text=i<7;
   const unsigned j=is_text?i:i-7;
   const unsigned off=j*4;
   const uint32_t offset=big32(file.data()+(is_text?0:0x1c)+off);
   const uint32_t base=big32(file.data()+(is_text?0x48:0x64)+off);
   const uint32_t n=big32(file.data()+(is_text?0x90:0xac)+off);
   if(i>=2){check(offset==0&&base==0&&n==0,"unexpected extra DOL sections");continue;}
   check(offset>=0x100&&uint64_t(offset)+n<=file.size()&&base==addr[i]&&n==length[i],"private DOL geometry changed");
   check(fnv(file.data()+offset,n)==hash[i],"SHA-pinned private original instruction image differs");
 }
 check(big32(file.data()+0xe0)==ENTRY,"wrong original interrupt init entrypoint");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1]),"invalid private original test DOL");
 nwii::analyzer::Analyzer a(exe);
 a.analyze({STOP});
 const auto&func=a.get_functions();
 // The synthetic terminal syscall is a basic block within the original entry.
 check(func.size()==4&&func.count(STOP)==1,"unexpected native guest function roots");
 for(auto pc:{ENTRY,MEMSET,FILL})check(func.count(pc)==1,"missing original interrupt/memset helper");
 expect(func.at(ENTRY),0x80526648u,MEMSET);
 expect(func.at(MEMSET),0x80004450u,FILL);
 check(func.at(MEMSET).instructions.size()==12u,"incomplete original memset wrapper");
 check(func.at(FILL).instructions.size()==45u,"incomplete original __fill_mem");
 const auto&main=func.at(ENTRY).instructions;
 check(main.size()==14u&&main[12].address==STOP&&main[12].opcode==0x44000002u,
       "original interrupt prefix synthetic boundary changed");
 nwii::recomp::RecompilerConfig c;c.output_dir=dir.string();c.split_output=false;
 nwii::recomp::Recompiler compiler(a,nullptr,c);
 auto paths=compiler.generate_cpp(ENTRY);
 check(paths.size()==1&&paths[0]=="output.cpp","unrecognized generated C++ output");
 std::cout<<"PASS: V50 original interrupt prefix + memset + __fill_mem emitted; roots="<<func.size()<<'\n';
 return 0;
}catch(const std::exception&e){std::cerr<<"V50 native generator error: "<<e.what()<<'\n';return 1;}
