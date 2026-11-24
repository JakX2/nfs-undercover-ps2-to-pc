#include "wii_v423_synthetic_program.h"
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace undercover::wii::v423;
int main(int argc,char** argv){
    if(argc!=3)throw std::runtime_error("expected fresh output directory and split mode");
    const std::filesystem::path dir=argv[1];const std::string mode=argv[2];
    if(!std::filesystem::is_directory(dir)||!std::filesystem::is_empty(dir)||(mode!="split"&&mode!="nonsplit"))throw std::runtime_error("invalid output");
    nwii::loader::Executable exe;exe.entry_point=Entry;
    auto add=[&](uint32_t address,const auto& data){exe.sections.push_back({address,uint32_t(data.size()),std::vector<uint8_t>(data.begin(),data.end()),true,false});};
    add(Entry,MainBytes);add(Vector,VectorBytes);
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({Vector});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";cfg.native_low_mem_entries.insert(Vector);
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(Entry).empty())throw std::runtime_error("no generated C++");
    std::ifstream f(dir/(cfg.split_output?"main_output.cpp":"output.cpp"));
    const std::string src((std::istreambuf_iterator<char>(f)),{});
    if(src.find("case 0x80000500: func_80000500(ctx); break;")==std::string::npos||src.find("case 0x8000402C: func_80004000(ctx); break;")==std::string::npos)throw std::runtime_error("missing vector or mtmsr resume dispatch case");
    std::cout<<"PASS: V423 generated explicit low-memory vector and mtmsr resume in "<<mode<<'\n';
}
