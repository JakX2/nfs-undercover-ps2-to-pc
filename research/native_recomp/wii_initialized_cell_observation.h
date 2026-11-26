#pragma once
#include "wii_initialized_dol_data_v1264.h"
#include <array>
#include <optional>

namespace undercover::wii {
using InitializedCellBytes=std::array<uint8_t,4>;

// This reads only an authenticated initialized data section, never
// assumes that a writable cell retained its initial file value.
inline std::optional<InitializedCellBytes> initialized_cell_bytes(
        std::span<const uint8_t> raw,uint32_t addr,unsigned width){
    if((width!=1u&&width!=2u&&width!=4u)||addr%width||
       addr<0x80004000u||uint64_t(addr)+width>0x81800000ull)return {};
    const auto ranges=initialized_dol_ranges(raw);
    for(const auto& range:ranges){
        if(addr<range.address||uint64_t(addr)+width>uint64_t(range.address)+range.size)continue;
        InitializedCellBytes result{};
        std::copy_n(raw.data()+range.file+(addr-range.address),width,result.begin());
        return result;
    }
    return {};
}

struct InitializedCellEvidence {
    bool pre_guest_matches_file=false;
    bool boundary_matches_file=false;
    bool sampled_values_equal=false;
};

// Endpoint observations only. Equality does not prove that no write
// occurred between samples. No guest load, state repair or memory write.
class InitializedCellObservation {
public:
    template<class C>bool begin(C& c,std::span<const uint8_t> original,uint32_t addr,unsigned width){
        if(cpu_||finished_)return false;
        const auto expected=initialized_cell_bytes(original,addr,width);
        if(!expected)return false;
        const auto cold=sample(c,addr,width);
        if(!cold)return false;
        file_=*expected;cold_=*cold;addr_=addr;width_=width;
        cpu_=&c;ticks_=c.inst_count;return true;
    }
    template<class C>std::optional<InitializedCellEvidence> finish(C& c,bool boundary_held){
        if(!cpu_||finished_||cpu_!=&c||!boundary_held||c.inst_count<=ticks_)return {};
        const auto live=sample(c,addr_,width_);
        if(!live)return {};
        finished_=true;
        return InitializedCellEvidence{cold_==file_,*live==file_,*live==cold_};
    }
private:
    const void* cpu_=nullptr;uint64_t ticks_=0;uint32_t addr_=0;unsigned width_=0;
    bool finished_=false;InitializedCellBytes file_{},cold_{};
    template<class C>static std::optional<InitializedCellBytes> sample(C& c,uint32_t addr,unsigned width){
        if((width!=1u&&width!=2u&&width!=4u)||addr%width||
           addr<0x80004000u||uint64_t(addr)+width>0x81800000ull)return {};
        const auto* base=c.mmu.get_ptr(addr);if(!base)return {};
        InitializedCellBytes result{};
        for(unsigned i=0;i<width;++i){
            const auto* p=c.mmu.get_ptr(addr+i);
            if(!p||reinterpret_cast<uintptr_t>(p)!=reinterpret_cast<uintptr_t>(base)+i)return {};
            result[i]=*p;
        }
        return result;
    }
};
}
