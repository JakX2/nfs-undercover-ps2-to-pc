#pragma once
#include <algorithm>
#include <cstdint>
#include <stdexcept>
namespace undercover::wii {
// Constant-space proof of ordered arena zero and tail flush operations.
// This is a read-only observer of the existing native flat RAM operations,
// not a hardware cache simulation. Arm only from a verified guest callsite.
class ArenaCacheRangeTrace {
public:
    static constexpr uint32_t Line=32u,Tail=0x40000u;
    enum class Phase{Idle,Zero,Flush,ScReady,Done,Failed};
    Phase phase()const noexcept{return phase_;}
    unsigned lanes()const noexcept{return lanes_;}
    uint64_t zeros()const noexcept{return zeros_;}
    uint64_t flushes()const noexcept{return flushes_;}
    unsigned failure()const noexcept{return failure_;}
    template<class Cpu>bool begin(Cpu& c,unsigned lane,uint32_t lo,uint32_t hi){
        if(failure_||!c.is_running||lane!=lanes_+1||lane>2||
           (phase_!=Phase::Idle&&phase_!=Phase::Done)||((lo|hi)&31u)||
           hi<=lo||hi-lo<Tail||!range(lane,lo,hi)||!mapped(c,lo-1,hi))return fail(1);
        if(context_&&context_!=&c)return fail(1);
        context_=&c;lo_=lo;hi_=hi;zero_next_=lo;flush_next_=hi-Tail;
        lower_=c.mmu.read8(lo-1);upper_=c.mmu.read8(hi);
        zero_base_=c.guest_dcbz_trace.count;flush_base_=c.guest_flush_count;
        if(uint64_t(flush_base_)+Tail/Line>0xffffffffu||zero_base_>UINT64_MAX-(hi-lo)/Line)return fail(1);
        msr_=c.msr;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];
        lane_=lane;phase_=Phase::Zero;return true;
    }
    void on_zero(uint32_t ea){
        if(phase_==Phase::Idle||phase_==Phase::Done)return;
        if(phase_!=Phase::Zero||(ea&~31u)!=zero_next_||zero_next_>=hi_)reject(2);
        zero_next_+=Line;++zeros_;
    }
    void on_flush(uint32_t ea){
        if(phase_==Phase::Idle||phase_==Phase::Done)return;
        if(phase_!=Phase::Flush||(ea&~31u)!=flush_next_||flush_next_>=hi_)reject(3);
        flush_next_+=Line;++flushes_;
    }
    template<class Cpu>bool begin_flush(Cpu& c,uint32_t a,uint32_t n){
        if(phase_!=Phase::Zero||!state(c)||zero_next_!=hi_||
           c.guest_dcbz_trace.count!=zero_base_+(hi_-lo_)/Line||
           c.guest_flush_count!=flush_base_||a!=hi_-Tail||n!=Tail||
           !cleared(c))return fail(4);
        phase_=Phase::Flush;return true;
    }
    template<class Cpu>bool ready_sc(Cpu& c){
        if(phase_!=Phase::Flush||!state(c)||flush_next_!=hi_||
           c.guest_dcbz_trace.count!=zero_base_+(hi_-lo_)/Line||
           uint64_t(c.guest_flush_count)!=uint64_t(flush_base_)+Tail/Line||
           c.guest_last_flush!=hi_-Line||!cleared(c))return fail(5);
        phase_=Phase::ScReady;return true;
    }
    template<class Cpu>bool finish(Cpu& c){
        if(phase_!=Phase::ScReady||!state(c)||
           c.guest_dcbz_trace.count!=zero_base_+(hi_-lo_)/Line||
           uint64_t(c.guest_flush_count)!=uint64_t(flush_base_)+Tail/Line||
           c.guest_last_flush!=hi_-Line||!cleared(c))return fail(6);
        ++lanes_;phase_=Phase::Done;return true;
    }
private:
    const void* context_=nullptr;
    Phase phase_=Phase::Idle;
    unsigned lanes_=0,lane_=0,failure_=0;
    uint32_t lo_=0,hi_=0,zero_next_=0,flush_next_=0,flush_base_=0;
    uint32_t msr_=0,sp_=0,r2_=0,r13_=0;
    uint64_t zero_base_=0,zeros_=0,flushes_=0;
    uint8_t lower_=0,upper_=0;
    bool fail(unsigned n){if(!failure_)failure_=n;phase_=Phase::Failed;return false;}
    [[noreturn]]void reject(unsigned n){fail(n);throw std::runtime_error("arena cache sequence rejected");}
    static bool range(unsigned lane,uint32_t lo,uint32_t hi){
        return lane==1?lo>0x80000000u&&hi<0x81800000u:lo>0x90000000u&&hi<0x94000000u;
    }
    template<class Cpu>static bool mapped(Cpu& c,uint32_t lo,uint32_t hi){
        auto* first=c.mmu.get_ptr(lo);auto* last=c.mmu.get_ptr(hi);
        return first&&last&&reinterpret_cast<uintptr_t>(last)>=reinterpret_cast<uintptr_t>(first)&&
            reinterpret_cast<uintptr_t>(last)-reinterpret_cast<uintptr_t>(first)==hi-lo;
    }
    template<class Cpu>bool state(Cpu& c)const{
        return !failure_&&context_==&c&&c.is_running&&c.msr==msr_&&c.gpr[1]==sp_&&
            c.gpr[2]==r2_&&c.gpr[13]==r13_&&lane_==lanes_+1;
    }
    template<class Cpu>bool cleared(Cpu& c)const{
        if(!mapped(c,lo_-1,hi_)||c.mmu.read8(lo_-1)!=lower_||c.mmu.read8(hi_)!=upper_)return false;
        const auto* p=c.mmu.get_ptr(lo_);
        return std::all_of(p,p+(hi_-lo_),[](uint8_t v){return v==0;});
    }
};
}
