// Independent native two-helper device ACK program, no original code.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <vector>
constexpr uint32_t H=0x80004000u,A=0x80005000u,B=0x80006000u,N=0x80007000u;
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
static std::vector<uint8_t> be(const std::vector<uint32_t>& words){
    std::vector<uint8_t> v;for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    auto add=[&](uint32_t a,const std::vector<uint32_t>& w){auto v=be(w);exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(H,{bl(H,A+4),bl(H+4,B),0x91070000u,0x60000000u,0x4e800020u});
    std::vector<uint32_t> saves;
    for(unsigned r=28;r<32;++r)saves.push_back(0x900b0000u|(r<<21)|(uint32_t(-4*int(32-r))&0xffffu));
    saves.push_back(0x4e800020u);add(A,saves);
    add(B,{0x910c0000u,0x2c090000u,0x41820008u,bl(B+12,N),0x4e800020u});
    add(N,{0x3860002au,0x4e800020u});
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans({{H,H+20},{A,A+20},{B,B+20},{N,N+8}});
    a.analyze({A,B,N});
    const auto& f=a.get_functions();
    assert(f.at(H).instructions.size()==5&&f.at(A).instructions.size()==5&&f.at(A+4).instructions.size()==4&&f.at(B).instructions.size()==5);
    for(const auto& [pc,fn]:f){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
    std::cout<<"V692_TRANSLATION split="<<cfg.split_output<<" independent_roots=5\n";
}
