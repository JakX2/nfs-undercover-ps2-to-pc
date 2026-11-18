// Original-free forward/backward tail thunk and local-branch regression.
#include "analyzer/analyzer.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>
static std::vector<uint8_t> be(std::initializer_list<uint32_t> words){
    std::vector<uint8_t> out;
    for(uint32_t v:words)for(unsigned n:{24u,16u,8u,0u})out.push_back(uint8_t(v>>n));
    return out;
}
static uint32_t b(uint32_t from,uint32_t to,bool link=false){
    return 0x48000000u|((to-from)&0x03fffffcu)|uint32_t(link);
}
int main(){
    constexpr uint32_t base=0x80010000u,body=base+0x10u,tail=base+0x18u,
        forward=base+0x1cu,local=base+0x20u,local_target=base+0x28u,interior=base+0x30u;
    const auto bytes=be({b(base,tail,true),b(base+4,forward,true),0x4e800020u,0x60000000u,
        0x3860002au,0x4e800020u,b(tail,body),b(forward,local),b(local,local_target),
        0x60000000u,0x38600011u,0x4e800020u,0x60000000u,b(interior+4u,local_target)});
    nwii::loader::Executable exe;exe.entry_point=base;
    exe.sections.push_back({base,uint32_t(bytes.size()),bytes,true,false});
    nwii::analyzer::Analyzer a(exe);a.analyze({body,local,interior});
    const auto& f=a.get_functions();
    for(uint32_t pc:{tail,forward}){
        assert(f.count(pc)&&f.at(pc).start_address==pc&&f.at(pc).instructions.size()==1);
    }
    assert(f.at(body).instructions.size()==2);
    for(const auto& [pc,fn]:f){(void)pc;assert(fn.hle_hook_name.empty());}
    assert(f.at(local).instructions.size()==3); // nonexplicit local target
    // An interior branch is not an entry thunk, even with an explicit root.
    auto bytes2=be({0x60000000u,b(base+4,body),0x60000000u,0x60000000u,0x38600007u,0x4e800020u});
    nwii::loader::Executable second;second.entry_point=base;
    second.sections.push_back({base,uint32_t(bytes2.size()),bytes2,true,false});
    nwii::analyzer::Analyzer a2(second);a2.analyze({body});
    assert(a2.get_functions().at(base).instructions.size()==4);
    // Without the explicit root the same backward branch remains local.
    nwii::analyzer::Analyzer a3(exe);a3.analyze();
    assert(a3.get_functions().at(tail).instructions.size()==3);
    std::cout<<"PASS: explicit tail thunks preserve guest entry, backward/forward targets, ordinary internal branches\n";
}
