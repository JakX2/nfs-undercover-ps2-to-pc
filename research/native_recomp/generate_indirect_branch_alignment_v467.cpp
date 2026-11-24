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
    auto branch=[](unsigned xo,unsigned bo,unsigned bi,unsigned lk){
        return (19u<<26)|(bo<<21)|(bi<<16)|(xo<<1)|lk;
    };
    // Distinct direct roots; test all four linked/nonlinked forms plus
    // conditional LR/CTR branches. Fallthrough has an independent tail.
    add(0x80004000u,{branch(16,20,0,0)});
    add(0x80004100u,{branch(16,20,0,1)});
    add(0x80004200u,{branch(528,20,0,0)});
    add(0x80004300u,{branch(528,20,0,1)});
    add(0x80004400u,{branch(16,12,2,0),0x480fbbfcu});
    add(0x80004500u,{branch(528,12,2,1),0x480fbafcu});
    add(0x80004600u,{branch(16,16,0,1),0x480fb9fcu});
    add(0x80100000u,{0x4e800020u});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({0x80004100u,0x80004200u,0x80004300u,0x80004400u,0x80004500u,0x80004600u,0x80100000u});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("no generated C++");
    std::cout<<"PASS: generated independent indirect branch alignment in "<<mode<<'\n';
}
