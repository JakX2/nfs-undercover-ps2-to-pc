#pragma once
#include "wii_ipc_client_witness_v623.h"
#include <string_view>
namespace undercover::wii {
struct StmPath {uint32_t addr,kind;};
struct StmPrefixExpectations {
    std::array<uint32_t,7> bridge;
    VectorEdge stm,open;
    std::array<StmPath,8> paths;
    unsigned path_count;
    uint32_t irq_handler;
};
// Complete-image observation only: no SDA seeding, pathname replacement,
// IOS service, synthetic return or guest writes.
class StmPrefixWitness {
public:
    static constexpr uint32_t Begin=0x8052094cu,Stm=0x8052b034u,Open=0x80519944u;
    explicit StmPrefixWitness(const StmPrefixExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    unsigned path_kind()const noexcept{return kind_;}
    template<class Cpu>bool begin(Cpu& c,bool ipc_returned){
        auto s=NativeIosBinding::cold_snapshot();
        using W=IpcClientWitness;
        if(stage_||error_||!ipc_returned||!c.is_running||c.pc!=Begin||c.lr!=Begin||
           c.gpr[3]!=0||c.gpr[1]!=W::Stack||c.gpr[13]!=W::Sda||!(c.msr&0x8000u)||c.dispatch_saved_ctx||
           !s||!idle(*s)||!bridge(c)||!e_.path_count||e_.path_count>e_.paths.size()||
           !equal(c,W::IrqGlobal,W::Table)||!equal(c,W::Table+108u,e_.irq_handler)||
           !equal(c,W::MaskA,0xf7fff7e0u)||!equal(c,W::MaskB,0))return fail(1);
        for(unsigned i=0;i<32;++i){
            if(!mapped(c,W::Table+4*i,4))return fail(1);
            irqs_[i]=c.mmu.read32(W::Table+4*i);
        }
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;tick_=c.inst_count;
        before_=*s;ctx_=&c;stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        using W=IpcClientWitness;
        auto s=NativeIosBinding::cold_snapshot();
        if(error_||stage_<1||stage_>2||ctx_!=&c||!c.is_running||c.pc!=addr||
           c.dispatch_saved_ctx||c.inst_count<=tick_||c.inst_count-tick_>4096||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           !s||!same(*s,before_)||!bridge(c)||!equal(c,W::IrqGlobal,W::Table)||
           !equal(c,W::MaskA,0xf7fff7e0u)||!equal(c,W::MaskB,0))return fail(2);
        for(unsigned i=0;i<32;++i)if(!equal(c,W::Table+4*i,irqs_[i]))return fail(2);
        const auto& e=stage_==1?e_.stm:e_.open;
        const uint32_t want=stage_==1?Stm:Open,lr=stage_==1?0x80520968u:0x8052b090u;
        if(e.pc!=want||e.lr!=lr||addr!=want||c.lr!=lr||
           !equal(c,addr,e.entry_word)||!equal(c,lr-4,e.branch_word))return fail(3);
        if(stage_==1){
            if(c.gpr[1]!=sp_)return fail(4);
        }else{
            if(c.gpr[1]>=sp_||sp_-c.gpr[1]>256u||c.gpr[4]!=0)return fail(4);
            unsigned found=0;
            for(unsigned i=0;i<e_.path_count;++i){
                const auto p=e_.paths[i];
                if(p.addr!=c.gpr[3])continue;
                const std::string_view path=p.kind==1?"/dev/stm/immediate":p.kind==2?"/dev/stm/eventhook":"";
                if(path.empty()||!mapped(c,p.addr,unsigned(path.size()+1)))return fail(5);
                for(unsigned j=0;j<path.size();++j)if(c.mmu.read8(p.addr+j)!=uint8_t(path[j]))return fail(5);
                if(c.mmu.read8(p.addr+uint32_t(path.size())))return fail(5);
                ++found;kind_=p.kind;
            }
            if(found!=1)return fail(5);
        }
        tick_=c.inst_count;++stage_;return true;
    }
private:
    StmPrefixExpectations e_;
    const void* ctx_=nullptr;
    unsigned stage_=0,error_=0,kind_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;
    uint64_t tick_=0;
    std::array<uint32_t,32> irqs_{};
    ColdIpcSnapshot before_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool idle(const ColdIpcSnapshot& s){
        using M=IpcMailbox;using H=HollywoodIrq;
        return !s.queued&&!s.replies&&!s.event&&!s.steps&&
            (s.control&(M::IY1|M::IY2))&&!(s.control&(M::X1|M::Y1|M::Y2))&&
            !(s.flags&H::IPC_PPC)&&s.irq_mask==H::IPC_PPC&&
            (s.pi_mask&H::PI_HOLLYWOOD)&&!(s.pi_cause&s.pi_mask);
    }
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&a.steps==b.steps&&
            a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>bool bridge(Cpu& c)const{
        for(unsigned i=0;i<e_.bridge.size();++i)if(!equal(c,Begin+4*i,e_.bridge[i]))return false;
        return true;
    }
};
}
