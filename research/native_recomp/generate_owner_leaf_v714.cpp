// Private authenticated original leaf input, separately authored caller.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <vector>
#include "owner_leaf_input.h"
static std::vector<uint8_t> be(const std::vector<uint32_t>& words){
    std::vector<uint8_t> v;for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    auto add=[&](uint32_t a,const auto& words){std::vector<uint32_t> w(words.begin(),words.end());auto v=be(w);exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(H,caller);add(D,disable_words);add(T,time_words);add(R,restore_words);
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans({{H,H+24},{D,D+4*disable_words.size()},{T,T+4*time_words.size()},{R,R+4*restore_words.size()}});
    a.analyze({D,T,R});
    assert(a.get_functions().size()==4);
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
    std::cout<<"V714_TRANSLATION split="<<cfg.split_output<<" independent_roots=4\n";
}
