#pragma once
#include "wii_open_epoch_v1361.h"
#include <array>
#include <string_view>
namespace undercover::wii {
// Device-side gate only. The caller must authenticate the actual original
// IPC interrupt handler and its return before authorizing writes/service.
// Does not change the guest thread, MSR, PC, or synthesize an IRQ entry.
class ColdOpenReplyGate {
public:
    using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
    explicit ColdOpenReplyGate(unsigned first_kind=0):epoch_(first_kind){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    bool begin(uint32_t physical_request,unsigned kind,bool authorized){
        const auto s=B::cold_snapshot();
        if(stage_||error_||!authorized||!s||!physical_request||(physical_request&31u)||
           !epoch_.acknowledged_descriptors(kind)||
           s->ppc!=physical_request||s->queued||s->event||s->steps!=epoch_.ack_steps()||s->replies!=1u||
           (s->control&(M::X1|M::Y1|M::Y2))!=M::Y2||!(s->control&M::IY2)||
           !(s->control&M::IY1)||s->irq_mask!=H::IPC_PPC||!(s->flags&H::IPC_PPC)||
           !(s->pi_mask&H::PI_HOLLYWOOD)||!(s->pi_cause&H::PI_HOLLYWOOD)||
           ((s->pi_cause&s->pi_mask)&~H::PI_HOLLYWOOD)||
           !B::read_physical_byte(physical_request+63u))return fail(1);
        request_=physical_request;kind_=kind;ack_=*s;
        for(unsigned i=0;i<8;++i){
            auto v=B::read_physical_word(request_+4*i);if(!v)return fail(1);words_[i]=*v;
        }
        if(words_[0]!=S::Open||words_[4]!=0u||!path_ok())return fail(1);
        stage_=1;return true;
    }
    bool boundary(bool authorized)const{
        const auto s=B::cold_snapshot();
        return authorized&&!error_&&stage_>=1u&&stage_<=3u&&s&&same(*s,expected(stage_))&&epoch_.acknowledged_descriptors(kind_)&&request_ok(false);
    }
    bool write(uint32_t addr,uint32_t value,uint32_t msr,bool authorized){
        if((stage_!=1u&&stage_!=2u)||!boundary(authorized)||(msr&0x8000u)||
           (addr&0xc0000000u)==0x40000000u)return fail(2);
        const uint32_t a=addr&0x3fffffffu;
        const auto offset=stage_==1u?M::PPCCTRL:H::PPC_FLAG;
        const auto expected_value=stage_==1u?ack_.control:H::IPC_PPC;
        if((a!=IosBus::IPC+offset&&a!=IosBus::MIRROR+offset)||value!=expected_value)return fail(2);
        try{if(!B::write32(addr,value))return fail(2);}
        catch(const std::exception&){return fail(2);}
        ++stage_;
        if(!boundary(authorized))return fail(2);
        return true;
    }
    bool publish(uint32_t msr,bool authenticated_handler_return){
        if(stage_!=3u||!boundary(authenticated_handler_return)||(msr&0x8000u))return fail(3);
        const auto step=B::service_at_guest_boundary(msr);
        const auto s=B::cold_snapshot();
        auto want=expected(3u);want.control|=M::Y1;want.arm=request_;
        want.flags|=H::IPC_PPC;want.pi_cause|=H::PI_HOLLYWOOD;want.steps=epoch_.reply_steps();want.replies=0;
        if(!step||step->progress!=S::Pump::Replied||!step->broadway_irq_level||step->guest_exception_ready||
           step->serviced_steps!=epoch_.reply_steps()||!s||!same(*s,want)||!request_ok(true)||
           !epoch_.acknowledged_descriptors(kind_))return fail(3);
        reply_=*s;stage_=4;return true;
    }
    bool reply_pending(bool authorized)const{
        const auto s=B::cold_snapshot();
        return stage_==4u&&!error_&&authorized&&s&&same(*s,reply_)&&epoch_.acknowledged_descriptors(kind_)&&request_ok(true);
    }
private:
    OpenTransactionEpoch epoch_;
    ColdIpcSnapshot ack_{},reply_{};
    std::array<uint32_t,8> words_{};
    uint32_t request_=0;unsigned kind_=0,stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    ColdIpcSnapshot expected(unsigned stage)const{
        auto s=ack_;
        if(stage>=2u)s.control&=~M::Y2;
        if(stage>=3u){s.flags&=~H::IPC_PPC;s.pi_cause&=~H::PI_HOLLYWOOD;}
        return s;
    }
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    bool path_ok()const{
        const std::string_view path=kind_==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
        const uint32_t a=words_[3];
        if(!a||uint64_t(a)+path.size()+1u>0x100000000ull)return false;
        for(unsigned i=0;i<path.size();++i)
            if(B::read_physical_byte(a+i)!=uint8_t(path[i]))return false;
        return B::read_physical_byte(a+uint32_t(path.size()))==0u;
    }
    bool request_ok(bool replied)const{
        for(unsigned i=0;i<8;++i){
            auto expected_word=words_[i];
            if(replied&&i<3u)expected_word=i==0u?uint32_t(S::Reply):i==1u?epoch_.result_fd():uint32_t(S::Open);
            if(B::read_physical_word(request_+4*i)!=expected_word)return false;
        }
        return path_ok();
    }
};
}
