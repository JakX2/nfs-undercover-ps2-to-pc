#pragma once
#include "wii_ipc_client_witness_v623.h"
#include "wii_open_sc_route_v637.h"
#include "open_cache_range_trace_v649.h"
#include <string_view>
namespace undercover::wii {
struct OpenRequestExpectations {
    VectorEdge entry,profile,disable,restore,flush,submit;
    uint32_t alloc_word,sc_word,flush_return_word;
};
// Cold first open only. Observe original allocation and request construction
// without submitting, servicing or completing the IOS request.
class OpenRequestWitness {
public:
    static constexpr uint32_t Open=0x80519944u,Profile=0x8051ad38u,Alloc=0x8051ab34u,
        Disable=0x805265acu,Restore=0x805265d4u,Flush=0x805222c0u,Submit=0x805195ecu;
    explicit OpenRequestWitness(const OpenRequestExpectations& e,unsigned first_kind=0):e_(e),epoch_(first_kind){}
    unsigned stage()const{return stage_;}unsigned failure()const{return error_;}
    uint32_t request()const{return request_;}
    template<class Cpu>bool begin(Cpu& c,unsigned kind,uint32_t heap_size){
        if(epoch_.second())return fail(1);
        return begin_epoch(c,kind,heap_size);
    }
    template<class Cpu>bool begin_second(Cpu& c,unsigned kind,uint32_t heap_size){
        if(!epoch_.second()||c.open_cache_range.phase()!=OpenCacheRangeTrace::Phase::Done||
           !begin_epoch(c,kind,heap_size)||!c.open_cache_range.rearm(c))return fail(1);
        return true;
    }
private:
    template<class Cpu>bool begin_epoch(Cpu& c,unsigned kind,uint32_t heap_size){
        using W=IpcClientWitness;
        const auto s=NativeIosBinding::cold_snapshot();
        path_=c.gpr[3];kind_=kind;
        if(stage_||error_||!c.is_running||c.dispatch_saved_ctx||!(c.msr&0x8000u)||
           c.gpr[4]||c.gpr[13]!=W::Sda||c.pc!=Open||!edge(c,e_.entry)||
           e_.entry.lr!=(epoch_.second()?0x8052b0b8u:0x8052b090u)||!epoch_.admits(kind)||!path_valid(c)||!s||!epoch_.quiet(*s)||
           !equal(c,W::IrqGlobal,W::Table)||!equal(c,W::MaskA,0xf7fff7e0u)||
           !equal(c,W::MaskB,0)||!mapped(c,W::Lo,8)||!mapped(c,W::Table,128))return fail(1);
        lo_=c.mmu.read32(W::Lo);hi_=c.mmu.read32(W::Hi);size_=heap_size;
        if(lo_<0x90000020u||(lo_&31u)||hi_>0x94000000u||size_<64u||
           size_>=W::HeapLimit||(size_&31u)||uint64_t(lo_)+size_>=hi_||
           !mapped(c,lo_-1u,size_+2u))return fail(1);
        lower_=c.mmu.read8(lo_-1u);upper_=c.mmu.read8(lo_+size_);
        for(unsigned i=0;i<32;++i)irqs_[i]=c.mmu.read32(W::Table+4*i);
        before_=*s;ctx_=&c;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;
        tick_=start_=c.inst_count;stage_=1;return true;
    }
public:
    template<class Cpu>bool observe(uint32_t addr,Cpu& c,OpenScRoute& sc){
        using R=OpenScRoute;using W=IpcClientWitness;
        const auto s=NativeIosBinding::cold_snapshot();
        if(error_||stage_<1||stage_>8||ctx_!=&c||!c.is_running||c.pc!=addr||
           c.dispatch_saved_ctx||c.inst_count<=tick_||c.inst_count-start_>200000u||
           c.gpr[1]>=sp_||sp_-c.gpr[1]>1024u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           c.msr!=(stage_==4?(msr_&~0x8000u):msr_)||!s||!same(*s,before_)||
           !path_valid(c)||!equal(c,W::Lo,lo_)||!equal(c,W::Hi,hi_)||
           !equal(c,W::IrqGlobal,W::Table)||!equal(c,W::MaskA,0xf7fff7e0u)||!equal(c,W::MaskB,0)||
           !mapped(c,lo_-1u,size_+2u)||c.mmu.read8(lo_-1u)!=lower_||c.mmu.read8(lo_+size_)!=upper_)return fail(2);
        for(unsigned i=0;i<32;++i)if(!equal(c,W::Table+4*i,irqs_[i]))return fail(2);
        switch(stage_){
        case 1:if(addr!=Profile||!edge(c,e_.profile)||c.lr!=0x8051998cu)return fail(3);
            break;
        case 2:if(addr!=Alloc||c.lr!=e_.profile.lr||!equal(c,Alloc,e_.alloc_word)||
                  !equal(c,Profile,e_.profile.entry_word)||c.gpr[4]<64u||c.gpr[4]>0x1000u)return fail(3);
            break;
        case 3:if(addr!=Disable||!edge(c,e_.disable)||c.lr!=0x8051ab64u)return fail(3);
            break;
        case 4:if(addr!=Restore||!edge(c,e_.restore)||c.lr!=0x8051ad14u||c.gpr[3]!=1u)return fail(3);
            break;
        case 5:{
            if(addr!=Flush||!edge(c,e_.flush)||c.lr!=R::Caller)return fail(3);
            const uint32_t a=canonical(c.gpr[3]),n=c.gpr[4];
            if(!n||n>0x1000u||!mapped(c,a,n)||a>path_||uint64_t(path_)+path_length()>uint64_t(a)+n)return fail(4);
            first_line_=a&~31u;lines_=((a&31u)+n+31u)/32u;flush_count_=c.guest_flush_count;
            if(uint64_t(flush_count_)+lines_>0xffffffffu||!c.open_cache_range.begin(c,c.gpr[3],n))return fail(4);
            break;}
        case 6:
            if(addr!=R::Call||c.lr!=R::Caller||!equal(c,addr,e_.sc_word)||
               c.guest_flush_count!=flush_count_+lines_||canonical(c.guest_last_flush)!=first_line_+(lines_-1u)*32u||!c.open_cache_range.ready_sc(c))return fail(4);
            try{sc.arm(addr,c);}catch(const std::exception&){return fail(5);}break;
        case 7:
            if(addr!=R::Caller||!equal(c,addr,e_.flush_return_word)||!sc.returned(c)||
               c.guest_flush_count!=flush_count_+lines_||!c.open_cache_range.finish(c))return fail(5);
            break;
        case 8:{
            if(addr!=Submit||!edge(c,e_.submit)||c.lr!=0x80519a3cu||sc.phase()!=R::Phase::Returned||c.open_cache_range.phase()!=OpenCacheRangeTrace::Phase::Done)return fail(3);
            const uint32_t req=canonical(c.gpr[3]);
            if(!req||(req&3u)||req<lo_||uint64_t(req)+32>uint64_t(lo_)+size_||!mapped(c,req,32)||
               c.mmu.read32(req)!=1u||canonical(c.mmu.read32(req+12u))!=path_||c.mmu.read32(req+16u)!=0)return fail(6);
            if(epoch_.second()&&((req&31u)||uint64_t(req)+64u>uint64_t(lo_)+size_||!mapped(c,req,64u)))return fail(6);
            request_=req;break;}
        default:return fail(2);
        }
        tick_=c.inst_count;++stage_;return true;
    }
private:
    OpenRequestExpectations e_;OpenTransactionEpoch epoch_;const void* ctx_=nullptr;
    unsigned stage_=0,error_=0,kind_=0;uint32_t request_=0,path_=0,lo_=0,hi_=0,size_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,first_line_=0,lines_=0,flush_count_=0;
    uint64_t start_=0,tick_=0;uint8_t lower_=0,upper_=0;
    std::array<uint32_t,32> irqs_{};ColdIpcSnapshot before_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t canonical(uint32_t a){return !a||(a&0xc0000000u)==0x40000000u?0u:(a&0x3fffffffu)|0x80000000u;}
    bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b)const{
        return epoch_.quiet(a)&&a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&a.steps==b.steps;
    }
    std::string_view pathname()const{return kind_==1?"/dev/stm/immediate":kind_==2?"/dev/stm/eventhook":"";}
    unsigned path_length()const{return unsigned(pathname().size()+1u);}
    template<class Cpu>bool path_valid(Cpu& c)const{
        const auto p=pathname();if(p.empty()||!mapped(c,path_,path_length()))return false;
        for(unsigned i=0;i<p.size();++i)if(c.mmu.read8(path_+i)!=uint8_t(p[i]))return false;
        return c.mmu.read8(path_+uint32_t(p.size()))==0;
    }
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        if(!n)return false;
        const uint64_t end=uint64_t(a)+n;
        if(!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==v;}
    template<class Cpu>static bool edge(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4u,e.branch_word);
    }
};
}
