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
    // Synthetic guest programs ARAM info, mask, addresses and count.
    // r8=count/direction, r9=MEM1 address, r10=MEM2 offset.
    add(0x80004000u,{0x3c60cc00u,0x60635000u,0x38800043u,0xb0830012u,
        0x38800040u,0xb083000au,0x91230020u,0x91430024u,0x91030028u,
        0x38e00010u,0x7ce903a6u,0xa0a3000au,0x4200fffcu,0x4e800020u});
    // Guest W1C acknowledgment, independent native function.
    add(0x80004100u,{0x3c60cc00u,0x60635000u,0x38800060u,0xb083000au,0x4e800020u});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({0x80004100u});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("no generated C++");
    std::cout<<"PASS: generated independent native loop and linked call in "<<mode<<'\n';
}
