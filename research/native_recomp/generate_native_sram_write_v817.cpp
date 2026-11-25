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
    // Independent guest immediate-transfer routine:
    // r3=CSR base, r5=control, r6=poll budget, r8=guest payload.
    // Load payload, issue DATA/CR stores, poll CR.TSTART, return
    // busy bit in r3 and the DATA register in r4.
    add(0x80004000u,{0x80880000u,0x90830010u,0x90a3000cu,0x80e3000cu,
        0x70e70001u,0x4182000cu,0x34c6ffffu,0x4082fff0u,0x80830010u,
        0x7ce33b78u,0x4e800020u});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("no generated C++");
    std::cout<<"PASS: generated independent native SRAM immediate transfer in "<<mode<<'\n';
}
