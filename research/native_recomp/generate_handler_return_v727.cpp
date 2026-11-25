// Independent native three-helper device ACK program, no original code.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <vector>
constexpr uint32_t X=0x8000b000u,H=0x80004000u,A=0x80005000u,B=0x80006000u,N=0x80007000u,D=0x80008000u,T=0x80009000u,R=0x8000a000u;
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
static std::vector<uint8_t> be(const std::vector<uint32_t>& words){
    std::vector<uint8_t> v;for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=X;
    auto add=[&](uint32_t a,const std::vector<uint32_t>& w){auto v=be(w);exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(X,{0x4e800421u,0x60000000u,0x4e800020u});
    add(H,{0x7c0802a6u,0x9001000cu,bl(H+8,A+4),bl(H+12,B),0x93fe0000u,0x8001000cu,0x7c0803a6u,0x4e800020u});
    std::vector<uint32_t> saves;
    for(unsigned r=28;r<32;++r)saves.push_back(0x900b0000u|(r<<21)|(uint32_t(-4*int(32-r))&0xffffu));
    saves.push_back(0x4e800020u);add(A,saves);
    add(B,{0x81070000u,0x91070000u,0x90c50000u,0x7c0802a6u,0x90010004u,bl(B+20,N),0x39800002u,0x398cffffu,0x2c0c0000u,0x4082fff8u,0x80010004u,0x7c0803a6u,0x4e800020u});
    add(N,{0x80850000u,0x910a0000u,0x7c0802a6u,0x90010008u,0x2c090000u,0x40820008u,bl(N+24,D),bl(N+28,T),0x38600000u,bl(N+36,R),0x80010008u,0x7c0803a6u,0x4e800020u});
    add(D,{0x7c0000a6u,0x7c000124u,0x38600000u,0x4e800020u});
    add(T,{0x7c6d42e6u,0x7c8c42e6u,0x7cad42e6u,0x7c032800u,0x4082fff0u,0x4e800020u});add(R,{0x7c0000a6u,0x7c000124u,0x4e800020u});
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans({{X,X+12},{H,H+32},{A,A+20},{B,B+52},{N,N+52},{D,D+16},{T,T+24},{R,R+12}});
    a.analyze({H,A,B,N,D,T,R});
    const auto& f=a.get_functions();
    assert(f.at(X).instructions.size()==3&&f.at(H).instructions.size()==8&&f.at(A).instructions.size()==5&&f.at(A+4).instructions.size()==4&&f.at(B).instructions.size()==13&&f.at(N).instructions.size()==13&&f.at(D).instructions.size()==4&&f.at(T).instructions.size()==6&&f.at(R).instructions.size()==3);
    for(const auto& [pc,fn]:f){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(X).empty());
    std::cout<<"V727_TRANSLATION split="<<cfg.split_output<<" independent_roots=9\n";
}
