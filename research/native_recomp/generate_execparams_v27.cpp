// Owner-local, original-free NWiiRecomp generator for Wii __OSGetExecParams.
// Emits native C++ only into an existing empty private output directory.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr uint32_t ENTRY=0x80523B1Cu,COPY=0x80004338u,STOP=0x80004900u;
void require(bool yes,const std::string& text){if(!yes)throw std::runtime_error(text);}
}
int main(int argc,char** argv)try{
 require(argc==3,"usage: generator PRIVATE_DOL EMPTY_OUTPUT_DIR");
 const std::filesystem::path out=argv[2];
 require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),
         "private output directory must exist and be empty");
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1]),"invalid test DOL");
 require(exe.entry_point==ENTRY&&exe.sections.size()==3,"wrong entry or sections");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({STOP});
 const auto& funcs=analyzer.get_functions();
 require(funcs.count(ENTRY)==1&&funcs.count(STOP)==1,
         "missing exec-params entry or explicit stop");
 const auto& code=funcs.at(ENTRY).instructions;
 require(code.size()==9 && code[0].address==ENTRY &&
         code.back().opcode==0x4E800020u,"short exec-params body");
 require(code[0].opcode==0x3CA08000u&&code[1].opcode==0x808530F0u,
         "exec-params low-memory source changed");
 require(code[4].opcode==0x38A0001Cu,"exec-params copy length changed");
 require(code[5].opcode>>26==18&&(code[5].opcode&3)==0,
         "exec-params tail call changed");
 uint32_t disp=code[5].opcode&0x03FFFFFCu;
 if(disp&0x02000000u)disp|=0xFC000000u;
 require(ENTRY+20u+disp==COPY,"exec-params tail target changed");
 require(funcs.count(COPY)==1&&funcs.at(COPY).instructions.size()==20u &&
         funcs.at(COPY).instructions.back().opcode==0x4E800020u,
         "original memcpy body missing or incomplete");
 require(code[6].opcode==0x38000000u&&code[7].opcode==0x90030000u,
         "exec-params zeroing path changed");
 const auto& stop=funcs.at(STOP).instructions;
 require(stop.size()==2&&stop[0].opcode==0x44000002u&&
         stop[1].opcode==0x4E800020u,"test-only stop changed");
 nwii::recomp::RecompilerConfig config;
 config.output_dir=out.string();config.split_output=false;
 nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
 const auto outputs=recomp.generate_cpp(ENTRY);
 require(outputs.size()==1&&outputs.at(0)=="output.cpp","unexpected emitter layout");
 std::cout<<"PASS: V27 original Wii exec-params native generator functions="<<funcs.size()<<'\n';
 return 0;
}catch(const std::exception& e){std::cerr<<"V27 generator: "<<e.what()<<'\n';return 1;}
