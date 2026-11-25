// Only the separately authored resume fixture is public. Loader bytes are owner-local.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_pair_input.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    auto add=[&](uint32_t address,const auto& words){
        std::vector<uint8_t> v;
        for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
        exe.sections.push_back({address,uint32_t(v.size()),std::move(v),true,false});
    };
    add(H,caller_words);add(S,save_words);add(R,restore_words);
    nwii::analyzer::Analyzer a(exe);
    a.set_trusted_code_spans({{H,H+4*caller_words.size()},{S,S+4*save_words.size()},{R,R+4*restore_words.size()}});
    a.analyze({S,R});assert(a.get_functions().size()==3);
    assert(a.get_functions().at(S).instructions.size()==save_words.size()&&a.get_functions().at(R).instructions.size()==restore_words.size());
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
    std::cout<<"V753_TRANSLATION split="<<cfg.split_output<<" roots=3\n";
}
