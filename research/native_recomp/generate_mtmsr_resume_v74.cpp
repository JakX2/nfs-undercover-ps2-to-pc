// Generate deliberately synthetic PPC entry/IRQ/stop functions.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <vector>
static std::vector<uint8_t> be(std::initializer_list<uint32_t> words){
    std::vector<uint8_t> v;
    for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
    return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    const std::filesystem::path dir=argv[1];
    const bool split=std::string(argv[2])=="split";
    constexpr uint32_t entry=0x80004000u,irq=0x80005000u,stop=0x80006000u;
    nwii::loader::Executable exe;exe.entry_point=entry;
    auto add=[&](uint32_t a,std::vector<uint8_t> v){
        exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});
    };
    auto branch=[](uint32_t a,uint32_t b){return 0x48000000u|((b-a)&0x03fffffcu);};
    add(entry,be({0x38800000u,0x60848000u,(31u<<26)|(4u<<21)|(146u<<1),
                  0x38a50001u,branch(entry+16u,stop)}));
    add(irq,be({0x38c60001u,0x4c000064u}));
    add(stop,be({0x44000002u,0x4e800020u}));
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({irq,stop});
    nwii::recomp::RecompilerConfig config;config.output_dir=dir.string();config.split_output=split;
    nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
    auto files=recomp.generate_cpp(entry);
    assert(!files.empty());
    std::ifstream file(dir/(split?"main_output.cpp":"output.cpp"));
    const std::string text((std::istreambuf_iterator<char>(file)),{});
    assert(text.find("case 0x8000400C: func_80004000(ctx); break;")!=std::string::npos);
    std::cout<<"PASS: exact native mtmsr continuation case in "<<argv[2]<<" dispatcher\n";
}
