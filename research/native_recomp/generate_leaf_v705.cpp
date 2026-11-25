// Independent native interrupt-disabled OS leaf program, no original code.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <vector>
constexpr uint32_t H=0x80004000u,D=0x80005000u,T=0x80006000u,R=0x80007000u;
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
static std::vector<uint8_t> be(const std::vector<uint32_t>& words){
    std::vector<uint8_t> v;for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    auto add=[&](uint32_t a,const std::vector<uint32_t>& w){auto v=be(w);exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(H,{bl(H,D),bl(H+4,T),0x38600000u,bl(H+12,R),0x60000000u,0x4e800020u});
    add(D,{0x7c0000a6u,0x7c000124u,0x38600000u,0x4e800020u});
    add(T,{0x7c8c42e6u,0x7c6d42e6u,0x4e800020u});
    add(R,{0x7c0000a6u,0x7c000124u,0x4e800020u});
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans({{H,H+24},{D,D+16},{T,T+12},{R,R+12}});
    a.analyze({D,T,R});
    assert(a.get_functions().size()==4);
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
    std::cout<<"V705_TRANSLATION split="<<cfg.split_output<<" independent_roots=4\n";
}
