#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_second_dispatch.h"
#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=Dispatcher;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    std::map<uint32_t,uint32_t> words;
    auto add=[&](uint32_t a,const auto& ws){
        spans.emplace_back(a,a+4u*uint32_t(ws.size()));
        for(auto w:ws){auto [i,inserted]=words.emplace(a,w);assert(inserted||i->second==w);a+=4u;}
    };
    add(Dispatcher,dispatcher_words);add(Scheduler,scheduler_words);add(Time,time_words);add(Disable,disable_words);add(Restore,restore_words);add(Handler,handler_words);add(Save,save_words);add(Completion,completion_words);add(Nested,nested_words);
    add(Transfer,transfer_words);
    if(TransferSave!=Save)add(TransferSave,transfer_save_words);
    add(TransferRestore,transfer_restore_words);add(Alarm,alarm_words);add(AlarmTimer,alarm_timer_words);add(CallbackRoot,callback_code);add(WirelessSetter,wireless_refusal);add(WirelessGetter,wireless_refusal);
    // Store overlapping aliases once in memory; their native function
    // entries are nevertheless independently analyzed and emitted.
    for(auto i=words.begin();i!=words.end();){
        const auto base=i->first;auto next=base;std::vector<uint8_t> v;
        while(i!=words.end()&&i->first==next){
            for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(i->second>>shift));
            next+=4u;++i;
        }
        exe.sections.push_back({base,next-base,std::move(v),true,false});
    }
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans(spans);
    std::vector<uint32_t> roots{Scheduler,Time,Disable,Restore,Handler,Save,Completion,Nested,Transfer,TransferRestore,Alarm,AlarmTimer,CallbackRoot,WirelessSetter,WirelessGetter};
    if(TransferSave!=Save)roots.push_back(TransferSave);
    a.analyze(roots);
    assert(a.get_functions().size()==TransferRootCount);
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(Dispatcher).empty());
    std::cout<<"V971_TRANSFER_TRANSLATION roots="<<TransferRootCount<<" split="<<cfg.split_output<<"\n";
}
