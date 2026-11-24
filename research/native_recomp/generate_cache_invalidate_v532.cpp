// Independent synthetic PowerPC functions; no original game code.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc,char** argv){
    if(argc!=3)throw std::runtime_error("expected fresh output directory and mode");
    const std::filesystem::path dir=argv[1];const std::string mode=argv[2];
    if(!std::filesystem::is_directory(dir)||!std::filesystem::is_empty(dir)||(mode!="split"&&mode!="nonsplit"))
        throw std::runtime_error("invalid output");
    nwii::loader::Executable exe;exe.entry_point=0x80004000u;
    auto add=[&](uint32_t address,std::initializer_list<uint32_t> words){
        std::vector<uint8_t> data;
        for(uint32_t w:words)for(int shift:{24,16,8,0})data.push_back(uint8_t(w>>shift));
        exe.sections.push_back({address,uint32_t(data.size()),data,true,false});
    };
    // Synthetic op31 cache operations, with both RA=0 and RA!=0.
    auto x=[](uint32_t xo,uint32_t ra,uint32_t rb){return (31u<<26)|(ra<<16)|(rb<<11)|(xo<<1);};
    add(0x80004000u,{x(1014,0,3),x(54,4,5),x(86,0,3),x(982,4,5),
                    x(470,0,3),x(470,4,5),x(598,0,0),x(854,0,0),0x4c00012cu,0x4e800020u});
    add(0x80004100u,{x(1014,4,5),0x4e800020u});
    add(0x80004200u,{x(470,0,3),x(470,4,5),0x4e800020u});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({0x80004100u,0x80004200u});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("no generated C++");
    std::cout<<"PASS: generated independent native cache operations in "<<mode<<'\n';
}
