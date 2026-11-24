#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace undercover::wii::v630 {
enum class R3Effect { Preserve,Read,Kill,Unknown };
// Conservative straight-line PPC GPR3 liveness classifier. The proof
// stops at every unknown instruction, branch, or prior read; a register
// read-modify-write is NOT a kill of an unused incoming value.
constexpr R3Effect effect(uint32_t w){
    const unsigned op=w>>26,rs=(w>>21)&31,ra=(w>>16)&31,rb=(w>>11)&31,xo=(w>>1)&1023;
    const auto classify=[](bool read,bool write){return read?R3Effect::Read:write?R3Effect::Kill:R3Effect::Preserve;};
    switch(op){
    case 14:case 15: // addi/addis
    case 32:case 34:case 40:case 42: // non-update integer loads
        return classify(ra==3,rs==3);
    case 33:case 35:case 41:case 43: // update loads
        if(!ra||ra==rs)return R3Effect::Unknown;
        return classify(ra==3,rs==3);
    case 37:case 39:case 45: // update stores
        if(!ra)return R3Effect::Unknown;
        [[fallthrough]];
    case 36:case 38:case 44:
        return classify(rs==3||ra==3,false);
    case 10:case 11: // compare immediate
        return classify(ra==3,false);
    case 24:case 25:case 26:case 27:case 28:case 29:case 21: // logical immediates / rlwinm
        return classify(rs==3,ra==3);
    case 20: // rlwimi reads old destination
        return classify(rs==3||ra==3,ra==3);
    case 23: // rlwnm
        return classify(rs==3||rb==3,ra==3);
    case 19:
        return w==0x4c00012cu?R3Effect::Preserve:R3Effect::Unknown; // isync only
    case 31:
        switch(xo){
        case 19:case 83:case 339: // mfcr / mfmsr / mfspr
            return w&1?R3Effect::Unknown:classify(false,rs==3);
        case 146:case 467: // mtmsr / mtspr
            return w&1?R3Effect::Unknown:classify(rs==3,false);
        case 0:case 32: // cmp / cmpl
            return w&1?R3Effect::Unknown:classify(ra==3||rb==3,false);
        case 28:case 60:case 124:case 284:case 316:case 412:case 444:case 476:
            return classify(rs==3||rb==3,ra==3); // register logic
        default:return R3Effect::Unknown;
        }
    default:return R3Effect::Unknown;
    }
}
constexpr unsigned dead_prefix(std::span<const uint32_t> words){
    if(words.empty()||words.size()>16)return 0;
    for(unsigned i=0;i<words.size();++i){
        const auto e=effect(words[i]);
        if(e==R3Effect::Kill)return i+1;
        if(e!=R3Effect::Preserve)return 0;
    }
    return 0;
}
// Validate the actual original guest text before treating the entry
// register as dead. Only the exact dominating overwrite prefix is needed.
template<class Read>bool verify_dead_prefix(uint32_t pc,std::span<const uint32_t> words,Read read){
    const auto count=dead_prefix(words);
    if(!count||(pc&3u)||uint64_t(pc)+4u*count>0x100000000ull)return false;
    for(unsigned i=0;i<count;++i){
        const auto actual=read(pc+4*i);
        if(!actual||*actual!=words[i])return false;
    }
    return true;
}
}
