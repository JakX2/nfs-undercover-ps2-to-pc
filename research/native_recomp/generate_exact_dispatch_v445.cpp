// Independently authored sparse synthetic PPC control-flow graph.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main(int argc,char** argv){
    need(argc==3,"output directory and mode");
    const std::filesystem::path dir=argv[1];const std::string mode=argv[2];
    need(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"fresh output");
    need(mode=="split"||mode=="nonsplit","mode");
    nwii::loader::Executable exe;exe.entry_point=0x80004000u;
    auto add=[&](uint32_t pc,std::initializer_list<uint32_t> words){
        std::vector<uint8_t> bytes;
        for(uint32_t w:words)for(unsigned s:{24u,16u,8u,0u})bytes.push_back(uint8_t(w>>s));
        exe.sections.push_back({pc,uint32_t(bytes.size()),bytes,true,false});
    };
    // Root A jumps across root B to root C, which jumps backward to A+4.
    // Thus A's numerical bounds include a hole containing B, and its
    // back-edge case can steal the actual separately analyzed C entry.
    add(0x80004000u,{0x48000100u,0x38840001u,0x4e800020u});
    add(0x80004080u,{0x38840002u,0x38840004u,0x4e800020u});
    add(0x80004100u,{0x4bffff04u});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({0x80004080u,0x80004100u});
    const auto& fs=analyzer.get_functions();
    need(fs.size()==3&&fs.at(0x80004000u).instructions.size()==4&&
         fs.at(0x80004080u).instructions.size()==3&&
         fs.at(0x80004100u).start_address==0x80004100u,"sparse root geometry");
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    need(!recomp.generate_cpp(exe.entry_point).empty(),"generation");
    std::cout<<"V445_GENERATED mode="<<mode<<" sparse=1 roots=3\n";
}
