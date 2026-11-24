#pragma once
#include "wii_full_start_witness.h"
#include <bit>
#include <cmath>

namespace undercover::wii {
// Bounded continuation from the V419 hardware entry to the cache entry.
// Expected instruction words are generated only from the authenticated DOL.
struct HardwareEntry {
    uint32_t pc,lr;
    unsigned count;
    std::array<uint32_t,74> words;
};
struct HardwareExpectations {
    std::array<HardwareEntry,6> entries;
    uint32_t ps_seed,scalar_seed;
};
class FullHardwareWitness {
public:
    explicit FullHardwareWitness(const HardwareExpectations& e):e_(e){}
    unsigned stage() const noexcept{return stage_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||failed_)return false;
        begun_=true;last_=c.inst_count;sp_=c.gpr[1];msr_=c.msr;hid0_=c.hid0;hid2_=c.hid2;
        return true;
    }
    template<class Cpu> FullStartResult observe(uint32_t pc,Cpu& c){
        if(!begun_||failed_||stage_>=e_.entries.size()||!c.is_running||c.pc!=pc||c.inst_count<=last_)return invalid();
        const auto& s=e_.entries[stage_];
        if(pc!=s.pc||c.lr!=s.lr||!s.count||s.count>s.words.size()||!mapped(c,pc,s.count*4u))return invalid();
        for(unsigned i=0;i<s.count;++i)if(c.mmu.read32(pc+4u*i)!=s.words[i])return invalid();
        if(stage_==0u){
            if(c.gpr[1]!=sp_||c.msr!=(msr_|0x2000u)||c.hid0!=hid0_||c.hid2!=hid2_)return invalid();
        }else if(stage_==1u){
            if(c.hid2!=hid2_||c.hid0!=hid0_)return invalid();
        }else if(stage_==2u){
            if(c.gpr[3]!=(hid2_|0xa0000000u))return invalid();
        }else if(stage_==3u){
            if(c.hid2!=(hid2_|0xa0000000u)||c.hid0!=hid0_)return invalid();
        }else if(stage_==4u){
            if(!state(c)||c.gpr[3]!=0u||!mapped(c,e_.ps_seed,8u)||!mapped(c,e_.scalar_seed,8u))return invalid();
            const float ps=std::bit_cast<float>(c.mmu.read32(e_.ps_seed+4u));
            scalar_=(uint64_t(c.mmu.read32(e_.scalar_seed))<<32)|c.mmu.read32(e_.scalar_seed+4u);
            // The earlier V19 oracle covers ordinary finite inputs; do not
            // claim correct exceptional FP conversion on arbitrary payloads.
            if(!std::isfinite(ps)||!std::isfinite(std::bit_cast<double>(scalar_)))return invalid();
            ps1_=std::bit_cast<uint64_t>(double(ps));
        }else{
            if(!state(c)||c.inst_count-last_<e_.entries[4].count||c.fpscr!=uint32_t(scalar_))return invalid();
            for(unsigned i=0;i<32;++i)if(std::bit_cast<uint64_t>(c.fpr[i])!=scalar_||std::bit_cast<uint64_t>(c.ps1[i])!=ps1_)return invalid();
        }
        last_=c.inst_count;++stage_;
        return stage_==e_.entries.size()?FullStartResult::Complete:FullStartResult::Accepted;
    }
private:
    HardwareExpectations e_;
    unsigned stage_=0;
    bool begun_=false,failed_=false;
    uint32_t sp_=0,msr_=0,hid0_=0,hid2_=0;
    uint64_t last_=0,scalar_=0,ps1_=0;
    FullStartResult invalid(){failed_=true;return FullStartResult::Invalid;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&!(a&3u)&&uint64_t(a)+n<=0x100000000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> bool state(Cpu& c) const{
        if(c.gpr[1]!=sp_||c.msr!=(msr_|0x2000u)||c.hid2!=(hid2_|0xa0000000u)||c.hid0!=(hid0_|0x800u))return false;
        for(auto q:c.gqr)if(q)return false;
        return true;
    }
};
}
