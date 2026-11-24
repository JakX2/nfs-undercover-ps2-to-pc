#pragma once
#include "wii_boot_sc_route_v570.h"
#include "undercover/arena_cache_range_trace_v596.h"
namespace undercover::wii {
// A separate pair of one-shot routes. The original V570 DSP route remains
// unchanged and is not reset or reused. This class is activated only after
// the independently verified original arena entry and zero/flush witnesses.
class ArenaScPair {
public:
    static constexpr std::array<uint32_t,2> Callers{0x8052002cu,0x80520208u};
    explicit ArenaScPair(const std::array<uint8_t,28>& v):routes_{BootScRoute(v,Callers[0]),BootScRoute(v,Callers[1])}{}
    unsigned completed()const noexcept{return completed_;}
    bool failed()const noexcept{return failed_;}
    template<class Cpu>void arm(uint32_t pc,Cpu& c,ArenaCacheRangeTrace& cache){
        if(failed_||completed_>=2||armed_||pc!=BootScRoute::Call||c.lr!=Callers[completed_]||
           cache.lanes()!=completed_||!cache.ready_sc(c))reject();
        if(ctx_&&ctx_!=&c)reject();
        ctx_=&c;cache_=&cache;
        try{routes_[completed_].arm(pc,c);}
        catch(...){failed_=true;throw;}
        armed_=true;
    }
    template<class Cpu>bool vector_trace(uint32_t addr,Cpu& c){
        if(!armed_||completed_>=2||routes_[completed_].phase()!=BootScRoute::Phase::Executing)return false;
        try{return routes_[completed_].vector_trace(addr,c);}
        catch(...){failed_=true;throw;}
    }
    template<class Cpu,class Native,class Verify>bool dispatch(Cpu& c,Native native,Verify verify){
        const bool at=c.pc==BootScRoute::Call&&(c.lr==Callers[0]||c.lr==Callers[1]);
        if(!armed_){if(at)reject();return false;}
        if(failed_||completed_>=2||ctx_!=&c||!cache_||!at)reject();
        try{return routes_[completed_].dispatch(c,native,verify);}
        catch(...){failed_=true;throw;}
    }
    template<class Cpu>bool finish(Cpu& c){
        if(failed_||!armed_||completed_>=2||ctx_!=&c||!cache_||
           !routes_[completed_].returned(c)||!cache_->finish(c))reject();
        ++completed_;armed_=false;cache_=nullptr;return true;
    }
private:
    std::array<BootScRoute,2> routes_;
    unsigned completed_=0;bool armed_=false,failed_=false;
    const void* ctx_=nullptr;ArenaCacheRangeTrace* cache_=nullptr;
    [[noreturn]]void reject(){failed_=true;throw std::runtime_error("V598 arena SC pair rejected");}
};
}
