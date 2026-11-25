#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_epilogue_input.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=HandlerC;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    auto add=[&](uint32_t a,const auto& ws){
        std::vector<uint8_t> v;for(auto w:ws)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
        const uint32_t n=uint32_t(v.size());spans.emplace_back(a,a+n);exe.sections.push_back({a,n,std::move(v),true,false});
    };
    add(H,resume_words);add(J,epilogue_words);add(L,loader_words);add(E,enable_words);add(S,resched_words);add(D,disable_words);add(R,restore_words);add(G,guard_words);add(HandlerC,HandlerWords);add(HandlerRestore,HandlerRestoreWords);add(VectorRoot,vector_words);add(TrampolineRoot,trampoline_words);add(DispatcherRoot,dispatcher_stop);
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans(spans);a.analyze({H,J,E,S,D,R,G,L,HandlerRestore,VectorRoot,TrampolineRoot,DispatcherRoot});
    assert(a.get_functions().size()==13);
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    // The ordinary emitter skips low MEM1 exception entries unless explicitly admitted.
    cfg.native_low_mem_entries.insert(VectorRoot);
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(HandlerC).empty());
    std::cout<<"V935_TRANSLATION split="<<cfg.split_output<<" roots=13\n";
}
