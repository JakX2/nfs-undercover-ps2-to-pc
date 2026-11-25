#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_second_dispatch.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=Dispatcher;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    auto add=[&](uint32_t a,const auto& ws){
        std::vector<uint8_t> v;for(auto w:ws)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
        const uint32_t n=uint32_t(v.size());spans.emplace_back(a,a+n);exe.sections.push_back({a,n,std::move(v),true,false});
    };
    add(Dispatcher,dispatcher_words);add(Scheduler,scheduler_words);add(Time,time_words);add(Disable,disable_words);add(Restore,restore_words);add(Handler,handler_words);
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans(spans);a.analyze({Scheduler,Time,Disable,Restore,Handler});
    assert(a.get_functions().size()==6);
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(Dispatcher).empty());
    std::cout<<"V946_DISPATCH_TRANSLATION roots=6 split="<<cfg.split_output<<"\n";
}
