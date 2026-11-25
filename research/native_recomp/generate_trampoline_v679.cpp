// Independent PPC register-save and backward-tail translation control.
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
static uint32_t branch(uint32_t a,uint32_t b){return 0x48000000u|((b-a)&0x03fffffcu);}
static uint32_t store(unsigned op,unsigned rs,unsigned ra,unsigned d){return op<<26|rs<<21|ra<<16|(d&0xffffu);}
int main(int argc,char**argv){
    assert(argc==3);
    const bool split=std::string(argv[2])=="split";
    const std::filesystem::path dir=argv[1];
    constexpr uint32_t Entry=0x80004000u,Dispatcher=0x80004200u,Trampoline=0x80004300u;
    nwii::loader::Executable exe;exe.entry_point=Entry;
    auto add=[&](uint32_t a,std::vector<uint8_t> v){exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(Entry,be({branch(Entry,Trampoline)}));
    add(Dispatcher,be({0x44000002u,0x4e800020u}));
    // Save all non-argument integer registers to an independent test buffer.
    // This synthetic geometry is deliberately unrelated to game code.
    add(Trampoline,be({store(36,0,4,0),store(36,1,4,4),store(36,2,4,8),
                       store(47,6,4,24),branch(Trampoline+16,Dispatcher)}));
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({Dispatcher,Trampoline});
    const auto& f=analyzer.get_functions();
    assert(f.at(Entry).instructions.size()==1&&f.at(Dispatcher).instructions.size()==2&&f.at(Trampoline).instructions.size()==5);
    for(const auto& [pc,fn]:f){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig config;config.output_dir=dir.string();config.split_output=split;
    nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
    assert(!recomp.generate_cpp(Entry).empty());
    std::cout<<"V679_SYNTHETIC_TRANSLATION split="<<split<<" roots=3 register_save=1 backward_tail=1\n";
}
