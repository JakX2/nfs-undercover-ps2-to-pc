#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_callback_wireless.h"
#include <cassert>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    auto add=[&](uint32_t address,const auto& ws){
        std::vector<uint8_t> v;
        for(auto w:ws)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
        const uint32_t n=uint32_t(v.size());
        spans.emplace_back(address,address+n);
        exe.sections.push_back({address,n,std::move(v),true,false});
    };
    std::vector<uint32_t> entries;
    for(const auto& r:all_roots){add(r.address,r.words);if(r.address!=H)entries.push_back(r.address);}
    nwii::analyzer::Analyzer a(exe);
    a.set_trusted_code_spans(spans);a.analyze(entries);
    assert(a.get_functions().size()==all_roots.size());
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
}
