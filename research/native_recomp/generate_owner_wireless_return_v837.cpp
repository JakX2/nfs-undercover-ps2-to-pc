#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "owner_wireless_return.h"
#include <cassert>
#include <string>
#include <vector>
#include <map>
int main(int argc,char** argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=H;
    std::vector<std::pair<uint32_t,uint32_t>> spans;
    std::vector<uint32_t> entries;
    std::map<uint32_t,uint32_t> image;
    for(const auto& root:roots){
        spans.emplace_back(root.address,root.address+4u*uint32_t(root.words.size()));
        uint32_t a=root.address;
        for(auto w:root.words){auto [it,inserted]=image.emplace(a,w);assert(inserted||it->second==w);a+=4u;}
        if(root.address!=H)entries.push_back(root.address);
    }
    for(auto it=image.begin();it!=image.end();){
        const uint32_t a=it->first;std::vector<uint8_t> v;uint32_t next=a;
        while(it!=image.end()&&it->first==next){
            for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(it->second>>shift));
            next+=4;++it;
        }
        const uint32_t n=uint32_t(v.size());exe.sections.push_back({a,n,std::move(v),true,false});
    }
    nwii::analyzer::Analyzer a(exe);a.set_trusted_code_spans(spans);a.analyze(entries);
    assert(a.get_functions().size()==roots.size());
    for(const auto& [pc,fn]:a.get_functions()){(void)pc;assert(fn.hle_hook_name.empty());}
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    nwii::recomp::Recompiler recomp(a,nullptr,cfg);assert(!recomp.generate_cpp(H).empty());
}
