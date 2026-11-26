#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Validate a complete authenticated manifest without modifying guest RAM.
template<class M,class Rows>bool verify_private_words(M& m,const Rows& rows){
    for(auto row:rows){
        if((row.pc&3u)||row.pc<0x80000000u||row.pc>0x817ffffcu||
           !m.get_ptr(row.pc)||!m.get_ptr(row.pc+3u)||m.read32(row.pc)!=row.word)return false;
    }
    return true;
}
// Install only one previously authenticated private fixture expansion.
// Validate the complete extent before any mutation. Called exclusively
// during focused harness initialization, never by a native callback.
template<class M,class Rows>bool seed_private_expansion(M& m,const Rows& rows,uint32_t root,unsigned count){
    if(!count||count>256u||(root&3u)||root<0x80000000u||
       uint64_t(root)+4u*count>0x81800000ull)return false;
    std::array<uint32_t,256> words{};
    std::array<bool,256> seen{};
    unsigned found=0;
    for(auto row:rows){
        if(row.owner!=root){
            if(row.pc>=root&&uint64_t(row.pc)<uint64_t(root)+4u*count)return false;
            continue;
        }
        if(row.pc<root||(row.pc&3u)||(row.pc-root)/4u>=count)return false;
        const auto i=(row.pc-root)/4u;
        if(seen[i]||!m.get_ptr(row.pc)||!m.get_ptr(row.pc+3u))return false;
        seen[i]=true;words[i]=row.word;++found;
    }
    if(found!=count||m.read32(root)!=words[0])return false;
    for(unsigned i=0;i<count;++i)m.write32(root+4u*i,words[i]);
    for(unsigned i=0;i<count;++i)if(m.read32(root+4u*i)!=words[i])return false;
    return true;
}
}
