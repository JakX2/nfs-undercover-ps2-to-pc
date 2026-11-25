#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_exi_write.h"
#include <cassert>
#include <string>
#include <vector>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    std::vector<uint32_t> entries;
    for(const auto& root:roots){
        std::vector<uint8_t> v;
        for(auto w:root.words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
        const uint32_t n=uint32_t(v.size());
        spans.emplace_back(root.address,root.address+n);
        exe.sections.push_back({root.address,n,std::move(v),true,false});
        if(root.address!=H)entries.push_back(root.address);
    }
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans(spans);a.analyze(entries);
    assert(a.get_functions().size()==roots.size());
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
}
