#pragma once
#include <array>
#include <cstdint>
#include <cstddef>

namespace undercover::wii {
// Source-only witness for the first two linked original startup calls in a
// complete AOT image. The caller supplies authenticated expected words.
struct FullStartExpectations {
    uint32_t entry,register_init,hardware_init;
    std::array<uint32_t,2> entry_words;
    std::array<uint32_t,36> register_words;
    std::array<uint32_t,4> hardware_words;
    std::array<uint32_t,32> register_result;
};
enum class FullStartResult { Accepted, Complete, Invalid };
class FullStartWitness {
public:
    explicit FullStartWitness(const FullStartExpectations& expected):expected_(expected){}
    unsigned stage() const noexcept{return stage_;}
    template<class Cpu> FullStartResult observe(uint32_t addr,Cpu& cpu){
        if(failed_||stage_>=3u||cpu.pc!=addr||!cpu.is_running||
           !addr||(addr&3u))return invalid();
        if(stage_==0u){
            if(addr!=expected_.entry||!words_match(cpu,addr,expected_.entry_words))return invalid();
        }else if(stage_==1u){
            if(addr!=expected_.register_init||cpu.lr!=expected_.entry+4u||
               cpu.inst_count<=last_inst_||!words_match(cpu,addr,expected_.register_words))return invalid();
        }else{
            if(addr!=expected_.hardware_init||cpu.lr!=expected_.entry+8u||
               cpu.inst_count<last_inst_||cpu.inst_count-last_inst_<expected_.register_words.size()||
               cpu.gpr!=expected_.register_result||!words_match(cpu,addr,expected_.hardware_words))return invalid();
        }
        last_inst_=cpu.inst_count;++stage_;
        return stage_==3u?FullStartResult::Complete:FullStartResult::Accepted;
    }
private:
    FullStartExpectations expected_;
    unsigned stage_=0u;
    bool failed_=false;
    uint64_t last_inst_=0u;
    FullStartResult invalid() noexcept{failed_=true;return FullStartResult::Invalid;}
    template<class Cpu,std::size_t N> static bool words_match(Cpu& cpu,uint32_t base,const std::array<uint32_t,N>& words){
        if(uint64_t(base)+N*4u>0x100000000ull)return false;
        for(std::size_t i=0;i<N;++i){
            const auto a=base+uint32_t(i*4u);
            if(!cpu.mmu.get_ptr(a)||!cpu.mmu.get_ptr(a+3u)||cpu.mmu.read32(a)!=words[i])return false;
        }
        return true;
    }
};
}
