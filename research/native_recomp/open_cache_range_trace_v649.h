#ifndef UNDERCOVER_OPEN_CACHE_RANGE_TRACE_V649_H
#define UNDERCOVER_OPEN_CACHE_RANGE_TRACE_V649_H
#include <cstdint>
namespace undercover::wii {
// Independent bounded observer of the real native pathname DCBF operations.
// The global boot trace has already filled its 256-entry history by now.
// No guest memory or cache state is modified by this observer.
class OpenCacheRangeTrace {
public:
    enum class Phase{Idle,Flush,ScReady,Done,Failed};
    Phase phase()const noexcept{return phase_;}
    unsigned lines()const noexcept{return lines_;}
    static uint32_t canonical(uint32_t a) noexcept {
        if(!a||(a&0xc0000000u)==0x40000000u)return 0;
        return (a&0x3fffffffu)|0x80000000u;
    }
    template<class Cpu>bool begin(Cpu& c,uint32_t addr,uint32_t n){
        if(phase_!=Phase::Idle||!c.is_running||!n||n>0x1000u)return fail();
        const uint32_t a=canonical(addr);
        if(!a)return fail();
        const uint64_t end=uint64_t(a)+n;
        if(!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return fail();
        first_=next_=a&~31u;stop_=uint32_t((end+31u)&~31ull);
        auto* p=c.mmu.get_ptr(first_);auto* q=c.mmu.get_ptr(stop_-1u);
        if(!p||!q||reinterpret_cast<uintptr_t>(q)<reinterpret_cast<uintptr_t>(p)||
           reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)!=stop_-first_-1u)return fail();
        base_=c.guest_flush_count;
        if(uint64_t(base_)+(stop_-first_)/32u>0xffffffffull)return fail();
        context_=&c;phase_=Phase::Flush;return true;
    }
    // Explicit empty range for the independently authenticated deferred
    // STM lane. No cache line may be emitted, including a spurious DCBF.
    template<class Cpu>bool begin_empty(Cpu& c){
        if(phase_!=Phase::Idle||!c.is_running)return fail();
        first_=next_=stop_=0;base_=c.guest_flush_count;last_empty_=c.guest_last_flush;
        context_=&c;phase_=Phase::Flush;return true;
    }
    // Explicit rearm only after a completed range on this same CPU.
    // The global cache-operation counter is never reset.
    template<class Cpu>bool rearm(Cpu& c){
        if(phase_!=Phase::Done||context_!=&c||!c.is_running||
           uint64_t(c.guest_flush_count)<uint64_t(base_)+lines_)return fail();
        phase_=Phase::Idle;context_=nullptr;first_=next_=stop_=base_=last_empty_=0;lines_=0;
        return true;
    }
    void on_flush(uint32_t ea) noexcept {
        if(phase_==Phase::Idle||phase_==Phase::Done)return;
        if(phase_!=Phase::Flush||next_>=stop_||(canonical(ea)&~31u)!=next_){fail();return;}
        next_+=32u;++lines_;
    }
    void on_zero(uint32_t) noexcept {
        if(phase_!=Phase::Idle&&phase_!=Phase::Done)fail();
    }
    template<class Cpu>bool ready_sc(Cpu& c){
        if(phase_!=Phase::Flush||!complete(c))return fail();
        phase_=Phase::ScReady;return true;
    }
    template<class Cpu>bool finish(Cpu& c){
        if(phase_!=Phase::ScReady||!complete(c))return fail();
        phase_=Phase::Done;return true;
    }
private:
    Phase phase_=Phase::Idle;const void* context_=nullptr;
    uint32_t first_=0,next_=0,stop_=0,base_=0,last_empty_=0;unsigned lines_=0;
    bool fail() noexcept {phase_=Phase::Failed;return false;}
    template<class Cpu>bool complete(Cpu& c)const{
        return context_==&c&&c.is_running&&next_==stop_&&lines_==(stop_-first_)/32u&&
            uint64_t(c.guest_flush_count)==uint64_t(base_)+lines_&&
            (lines_?(canonical(c.guest_last_flush)&~31u)==stop_-32u:c.guest_last_flush==last_empty_);
    }
};
}
#endif
