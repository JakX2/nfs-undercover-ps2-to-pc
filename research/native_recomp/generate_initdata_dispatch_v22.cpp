// Independent owner-local NWiiRecomp generator for five genuine Wii data-init functions.
// Input must be created privately from an owner DOL by make_initdata_slice_v22.py.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
namespace {
constexpr uint32_t ENTRY=0x80004238u, FLUSH=0x80004304u, COPY=0x80004338u,
                   FILL=0x80004388u, SET=0x8000443cu, STOP=0x80004900u,
                   TABLE=0x80006420u;
constexpr std::array<uint32_t,6> FUNCS{ENTRY,FLUSH,COPY,FILL,SET,STOP};
void require(bool yes,const char* reason){if(!yes)throw std::runtime_error(reason);}
uint32_t target_of(const nwii::analyzer::Instruction& inst){
 const uint32_t w=inst.opcode;
 require((w>>26)==18&&(w&3)==1,"unexpected BL opcode");
 uint32_t offset=w&0x03fffffcu;
 if(offset&0x02000000u)offset|=0xfc000000u;
 return inst.address+offset;
}
void expect_call(const nwii::analyzer::Function& f,uint32_t pc,uint32_t destination){
 bool found=false;
 for(const auto& ins:f.instructions){
  if(ins.address==pc){require(target_of(ins)==destination,"call graph edge changed");found=true;}
 }
 require(found,"missing required callsite");
}
}
int main(int argc,char**argv)try{
 require(argc==3,"usage: generate_initdata_dispatch_v22 PRIVATE_DOL EMPTY_DIR");
 const std::filesystem::path out=argv[2];
 require(std::filesystem::is_directory(out) && std::filesystem::is_empty(out),
         "private output directory must be existing and empty");
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1]),"invalid private test DOL");
 require(exe.entry_point==ENTRY,"unexpected entry PC");
 require(exe.sections.size()==3,"test DOL must contain 2 text and 1 data sections");
 bool table=false;
 for(const auto& s:exe.sections){
   if(s.address==TABLE&&!s.is_text&&!s.is_bss&&s.data.size()==0xb0u)table=true;
 }
 require(table,"missing initialized data table section");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({STOP});
 const auto& funcs=analyzer.get_functions();
 if(funcs.size()!=FUNCS.size()){
  std::cerr<<"got "<<funcs.size()<<" function roots; expected "<<FUNCS.size()<<"\n";
  for(const auto& [pc,f]:funcs)std::cerr<<std::hex<<pc<<" size="<<std::dec<<f.instructions.size()<<'\n';
  throw std::runtime_error("unexpected analyzed function count");
 }
 for(auto pc:FUNCS)require(funcs.count(pc)==1,"required function missing");
 const auto& init=funcs.at(ENTRY);
 expect_call(init,0x80004280u,COPY);
 expect_call(init,0x8000428cu,FLUSH);
 expect_call(init,0x800042b8u,SET);
 expect_call(funcs.at(SET),0x80004450u,FILL);
 require(init.instructions.size()==42u,"init_data function incomplete");
 require(funcs.at(FLUSH).instructions.size()==13u,"cache flush helper incomplete");
 require(funcs.at(COPY).instructions.size()==20u,"memcpy helper incomplete");
 require(funcs.at(FILL).instructions.size()==45u,"fill_mem helper incomplete");
 require(funcs.at(SET).instructions.size()==12u,"memset wrapper incomplete");
 const auto& stop=funcs.at(STOP).instructions;
 require(stop.size()==2 && stop[0].opcode==0x44000002u && stop[1].opcode==0x4e800020u,
        "test-only synthetic termination body changed");
 nwii::recomp::RecompilerConfig config;
 config.output_dir=out.string(); config.split_output=false;
 nwii::recomp::Recompiler compiler(analyzer,nullptr,config);
 const auto paths=compiler.generate_cpp(ENTRY);
 require(paths.size()==1&&paths[0]=="output.cpp","unexpected generated C++ outputs");
 std::cout<<"PASS: emitted "<<funcs.size()<<" native PPC functions for owner-local __init_data\n";
 return 0;
}catch(const std::exception& e){
 std::cerr<<"V22 generator error: "<<e.what()<<'\n';return 1;
}
