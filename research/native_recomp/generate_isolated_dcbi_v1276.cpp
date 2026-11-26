// Independent synthetic PPC cache operations, not original game code.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
int main(int argc,char** argv){
    if(argc!=3)throw std::runtime_error("expected output directory and mode");
    const std::filesystem::path dir=argv[1];const std::string mode=argv[2];
    if(!std::filesystem::is_directory(dir)||!std::filesystem::is_empty(dir)||
       (mode!="split"&&mode!="nonsplit"))throw std::runtime_error("invalid output");
    nwii::loader::Executable exe;exe.entry_point=0x80004000u;
    auto x=[](uint32_t xo,uint32_t ra,uint32_t rb){return (31u<<26)|(ra<<16)|(rb<<11)|(xo<<1);};
    std::vector<uint8_t> data;
    for(uint32_t w:{x(470,0,3),x(470,4,5),x(86,0,3),x(598,0,0),0x4e800020u})
        for(unsigned shift:{24u,16u,8u,0u})data.push_back(uint8_t(w>>shift));
    exe.sections.push_back({exe.entry_point,uint32_t(data.size()),data,true,false});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({});
    nwii::recomp::RecompilerConfig config;config.output_dir=dir.string();config.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("no generated C++");
    std::cout<<"V1276_GENERATED mode="<<mode<<" synthetic=1\n";
}
