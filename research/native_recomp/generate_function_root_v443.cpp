// Synthetic backwards-tail function roots, no owner material.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
static constexpr uint32_t Low=0x80004000u,High=0x80004100u;
int main(int argc,char** argv){
    need(argc==4,"output, split mode, baseline or fixed");
    const std::filesystem::path dir=argv[1];const std::string mode=argv[2],version=argv[3];
    need(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),"fresh output");
    need((mode=="split"||mode=="nonsplit")&&(version=="baseline"||version=="fixed"),"mode");
    const bool fixed=version=="fixed";
    nwii::loader::Executable exe;exe.entry_point=Low;
    auto add=[&](uint32_t address,std::initializer_list<uint32_t> words){
        std::vector<uint8_t> bytes;
        for(uint32_t word:words)for(unsigned shift:{24u,16u,8u,0u})bytes.push_back(uint8_t(word>>shift));
        exe.sections.push_back({address,uint32_t(bytes.size()),bytes,true,false});
    };
    add(Low,{0x38840001u,0x4e800020u}); // addi r4,r4,1; blr
    add(High,{0x38840002u,0x4bfffefcu}); // addi r4,r4,2; b Low
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({High});
    const auto& fs=analyzer.get_functions();
    need(fs.count(Low)==1&&fs.count(High)==1,"function root coverage");
    need(fs.at(Low).start_address==Low&&fs.at(High).start_address==(fixed?High:Low),"root identity");
    const auto& hi=fs.at(High).instructions;
    need(hi.size()==4&&hi.front().address==Low&&hi.back().address==High+4u,"backward body preserved");
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    const auto outputs=recomp.generate_cpp(Low);need(!outputs.empty(),"generated output");
    std::string src;
    for(const auto& name:outputs){
        if(std::filesystem::path(name).extension()!=".cpp")continue;
        std::ifstream f(dir/name);
        src.append(std::istreambuf_iterator<char>(f),{});
    }
    auto count=[&](const std::string& needle){unsigned n=0;for(size_t p=0;(p=src.find(needle,p))!=std::string::npos;p+=needle.size())++n;return n;};
    need(count("trace_call(0x80004000, ctx)")==unsigned(fixed?1:2),"low trace identity");
    need(count("trace_call(0x80004100, ctx)")==unsigned(fixed?1:0),"high trace identity");
    std::cout<<"V443_ROOT_GENERATED mode="<<mode<<" version="<<version<<" body=1 trace_geometry=1\n";
}
