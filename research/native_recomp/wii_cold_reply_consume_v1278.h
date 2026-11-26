#pragma once
#include "wii_open_epoch_v1361.h"
#include <array>
namespace undercover::wii {
// Device-side witness for the actual second IPC handler. Every read/write
// is routed to the already bound native transport. Authorization belongs
// to the authenticated original instruction/call observer.
class ColdReplyConsumeGate {
public:
    using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
    explicit ColdReplyConsumeGate(unsigned first_kind=0):epoch_(first_kind){}
    unsigned stage()const{return stage_;}
    unsigned first_kind()const{return epoch_.first_kind();}
    unsigned failure()const{return error_;}
    unsigned arm_reads()const{return arm_reads_;}
    unsigned control_reads()const{return control_reads_;}
    unsigned invalidations()const{return invalidations_;}
    bool begin(uint32_t request,bool authorized){
        const auto s=B::cold_snapshot();
        if(stage_||error_||!authorized||!epoch_held()||!s||!request||(request&31u)||
           s->ppc!=request||s->arm!=request||s->steps!=epoch_.reply_steps()||s->replies||s->queued||s->event||
           (s->control&(M::X1|M::Y1|M::Y2))!=M::Y1||
           !(s->control&M::IY1)||!(s->control&M::IY2)||
           !(s->flags&H::IPC_PPC)||!(s->irq_mask&H::IPC_PPC)||
           (s->pi_cause&s->pi_mask)!=H::PI_HOLLYWOOD||
           !B::read_physical_byte(request+63u))return fail(1);
        request_=request;initial_=*s;
        for(unsigned i=0;i<8u;++i){
            auto v=B::read_physical_word(request+4u*i);if(!v)return fail(1);
            words_[i]=*v;
        }
        if(words_[0]!=S::Reply||words_[1]!=epoch_.result_fd()||words_[2]!=S::Open)return fail(1);
        stage_=1;return true;
    }
    bool boundary(bool authorized)const{
        const auto s=B::cold_snapshot();
        if(!authorized||!stage_||stage_>3u||error_||!epoch_held()||!s||!same(*s,expected()))return false;
        for(unsigned i=0;i<8u;++i)if(B::read_physical_word(request_+4u*i)!=words_[i])return false;
        return true;
    }
    std::optional<uint32_t> read(uint32_t address,uint32_t msr,bool authorized){
        if(!boundary(authorized)||(msr&0x8000u)||invalid_alias(address)){fail(2);return {};}
        const auto p=address&0x3fffffffu;
        unsigned* count=nullptr;uint32_t want=0;
        if(reg(p,M::ARMMSG)){count=&arm_reads_;want=request_;}
        else if(reg(p,M::PPCCTRL)){count=&control_reads_;want=expected().control;}
        else if(reg(p,H::PPC_FLAG)){count=&flag_reads_;want=expected().flags;}
        if(!count||*count>=64u){fail(2);return {};}
        const auto v=B::read32(address);
        if(!v||*v!=want){fail(2);return {};}
        ++*count;return v;
    }
    bool write(uint32_t address,uint32_t value,uint32_t msr,bool authorized){
        if(!boundary(authorized)||(msr&0x8000u)||invalid_alias(address))return fail(3);
        const auto p=address&0x3fffffffu;
        // In the original reply processor, PPCCTRL.Y1 is cleared first.
        // Hollywood's interrupt latch is independent and may remain pending
        // until the outer handler acknowledges it.
        if(stage_==1u){
            if(!reg(p,M::PPCCTRL)||!control_reads_||value!=initial_.control)return fail(3);
        }else if(stage_==2u){
            if(!reg(p,H::PPC_FLAG)||value!=H::IPC_PPC)return fail(3);
        }else return fail(3);
        try{if(!B::write32(address,value))return fail(3);}
        catch(const std::exception&){return fail(3);}
        ++stage_;
        if(!boundary(authorized))return fail(3);
        return true;
    }
    // An original DCInvalidateRange call must encompass the actual reply
    // header, and its native dcbi events must cover that entire range.
    // This gate never performs invalidation itself.
    template<class C>bool begin_invalidation(C& c,uint32_t address,uint32_t length,bool authorized){
        if(!boundary(authorized)||!arm_reads_||cache_cpu_||!length||length>0x1000u||
           invalid_alias(address)||(c.msr&0x8000u))return fail(4);
        const auto a=address&0x3fffffffu;const uint64_t end=uint64_t(a)+length;
        if(a>request_||end<uint64_t(request_)+12u||end>0x14000000ull)return fail(4);
        const auto first=a&~31u;const auto stop=uint32_t((end+31u)&~31ull);
        if(!B::read_physical_byte(first)||!B::read_physical_byte(stop-1u)||
           uint64_t(c.guest_data_invalidate_count)+(stop-first)/32u>0xffffffffull)return fail(4);
        cache_cpu_=&c;next_line_=first;stop_line_=stop;cache_count_=c.guest_data_invalidate_count;
        return true;
    }
    // Called immediately after a real native dcbi instruction by the
    // authenticated observer. Count + last address must agree, even when
    // the bounded history has saturated.
    template<class C>bool invalidated(C& c,uint32_t effective_address,bool authorized){
        if(!boundary(authorized)||cache_cpu_!=&c||cache_done_||
           next_line_>=stop_line_||invalid_alias(effective_address)||
           ((effective_address&0x3fffffffu)&~31u)!=next_line_||
           c.guest_data_invalidate_count!=cache_count_+1u||
           c.guest_last_data_invalidate!=(effective_address&~31u))return fail(5);
        ++cache_count_;next_line_+=32u;++invalidations_;return true;
    }
    template<class C>bool finish_invalidation(C& c,bool authorized){
        if(!boundary(authorized)||cache_cpu_!=&c||cache_done_||!invalidations_||
           next_line_!=stop_line_||c.guest_data_invalidate_count!=cache_count_)return fail(6);
        cache_done_=true;return true;
    }
    template<class C>bool ready_for_wakeup(C& c,bool authorized)const{
        // The queue/guest callsite and saved CPU frame are checked by the
        // external owner witness. Do not allow the cache proof to be reused.
        return boundary(authorized)&&stage_>=2u&&arm_reads_&&cache_done_&&
            cache_cpu_==&c&&c.guest_data_invalidate_count==cache_count_&&!(c.msr&0x8000u);
    }
private:
    OpenTransactionEpoch epoch_;
    bool epoch_held()const{return epoch_.valid()&&(!epoch_.second()||epoch_.acknowledged_descriptors(3u-epoch_.first_kind()));}
    ColdIpcSnapshot initial_{};std::array<uint32_t,8> words_{};
    const void* cache_cpu_=nullptr;uint32_t request_=0,next_line_=0,stop_line_=0,cache_count_=0;
    unsigned stage_=0,error_=0,arm_reads_=0,control_reads_=0,flag_reads_=0,invalidations_=0;
    bool cache_done_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool invalid_alias(uint32_t a){return (a&0xc0000000u)==0x40000000u;}
    static bool reg(uint32_t a,uint32_t offset){return a==IosBus::IPC+offset||a==IosBus::MIRROR+offset;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    ColdIpcSnapshot expected()const{
        auto s=initial_;
        if(stage_>=2u)s.control&=~M::Y1;
        if(stage_>=3u){s.flags&=~H::IPC_PPC;s.pi_cause&=~H::PI_HOLLYWOOD;}
        return s;
    }
};
}
