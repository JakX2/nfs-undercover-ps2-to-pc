// Original-free overlapping compiler-style GPR-save entries.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <vector>
constexpr uint32_t Entry=0x80004000u,Parent=0x80004100u,Alias=Parent+12u;
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
static std::vector<uint8_t> be(const std::vector<uint32_t>& words){
    std::vector<uint8_t> v;for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));return v;
}
int main(int argc,char** argv){
    assert(argc==3);const bool split=std::string(argv[2])=="split";
    nwii::loader::Executable exe;exe.entry_point=Entry;
    auto add=[&](uint32_t a,const std::vector<uint32_t>& w){auto v=be(w);exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});};
    add(Entry,{bl(Entry,Parent),0x396b0100u,bl(Entry+8,Alias),0x44000002u,0x4e800020u});
    std::vector<uint32_t> saves;
    for(unsigned r=14;r<32;++r)saves.push_back(0x900b0000u|(r<<21)|((uint32_t(-4*int(32-r)))&0xffffu));
    saves.push_back(0x4e800020u);add(Parent,saves);
    nwii::analyzer::Analyzer a(exe);
    // Only the sized parent is trusted. The call target inside it must be
    // discovered as a native overlapping entry, not an exclusive span.
    a.set_trusted_code_spans({{Entry,Entry+20},{Parent,Parent+4*uint32_t(saves.size())}});
    a.analyze({Parent});
    const auto& f=a.get_functions();
    assert(f.at(Parent).instructions.size()==19&&f.at(Alias).instructions.size()==16);
    assert(f.at(Parent).start_address==Parent&&f.at(Alias).start_address==Alias&&f.at(Alias).hle_hook_name.empty());
    nwii::recomp::RecompilerConfig config;config.output_dir=argv[1];config.split_output=split;
    nwii::recomp::Recompiler recomp(a,nullptr,config);
    assert(!recomp.generate_cpp(Entry).empty());
    std::cout<<"V685_SHARED_ALIAS_TRANSLATION split="<<split<<" parent=19 alias=16 independent_entries=1\n";
}
