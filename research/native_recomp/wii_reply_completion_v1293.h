#pragma once
#include "wii_nested_wake_return_v1291.h"
namespace undercover::wii {
// Device-only continuation after the original wake return. Authorize each
// access from the later original handler instruction witness, not from the
// host. Never inject another response or step IOS.
class ReplyCompletionGate{
public:
    using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned writes()const{return writes_;}
    template<class C>bool begin(C& c,const ReplyProcessorWitness& body,const WakeReadyWitness& ready,
                                const NestedWakeReturnWitness& nested,ExternalReturnWitness& frame,
                                uint32_t queue,uint32_t request,bool authorized){
        const auto s=B::cold_snapshot();
        if(stage_||error_||!authorized||!s||!nested.returned_at(c,ready,true)||
           !body.postwake_ready(c,frame,queue,request,true)||!ready.ready_held(c,true)||
           s->ppc!=request||s->arm!=request||s->steps!=2u||s->queued||s->replies||s->event||
           (s->control&(M::X1|M::Y1|M::Y2))||!(s->control&M::IY1)||!(s->control&M::IY2)||
           !(s->irq_mask&H::IPC_PPC)||!request||(request&31u))return fail(1);
        const bool pending=bool(s->flags&H::IPC_PPC);
        if((s->pi_cause&s->pi_mask)!=(pending?H::PI_HOLLYWOOD:0u)||
           bool(s->pi_cause&H::PI_HOLLYWOOD)!=pending)return fail(1);
        for(unsigned i=0;i<words_.size();++i){
            auto w=B::read_physical_word(request+4u*i);if(!w)return fail(1);words_[i]=*w;
        }
        if(words_[0]!=S::Reply||words_[1]!=0u||words_[2]!=S::Open)return fail(1);
        cpu_=&c;ready_=&ready;mail_=*s;request_=request;tick_=c.inst_count;
        stage_=pending?1u:2u;return true;
    }
    template<class C>bool boundary(C& c,bool authorized)const{
        auto s=B::cold_snapshot();
        if(!authorized||!stage_||stage_>2u||error_||cpu_!=&c||!ready_||
           !ready_->ready_context_held(c,true)||!s||!same_scheduler_ipc_snapshot(*s,mail_)||
           c.inst_count<tick_||c.inst_count-tick_>2048u)return false;
        for(unsigned i=0;i<words_.size();++i)if(B::read_physical_word(request_+4u*i)!=words_[i])return false;
        return true;
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t address,bool authorized){
        if(!boundary(c,authorized)||bad_alias(address)||reads_>=64u){fail(2);return {};}
        const auto p=address&0x3fffffffu;uint32_t want=0;
        if(reg(p,M::PPCCTRL))want=mail_.control;
        else if(reg(p,H::PPC_FLAG))want=mail_.flags;
        else if(reg(p,M::ARMMSG))want=request_;
        else{fail(2);return {};}
        const auto v=B::read32(address);if(!v||*v!=want){fail(2);return {};}
        ++reads_;return v;
    }
    template<class C>bool write(C& c,uint32_t address,uint32_t value,bool authorized){
        if(stage_!=1u||!boundary(c,authorized)||bad_alias(address)||
           !reg(address&0x3fffffffu,H::PPC_FLAG)||value!=H::IPC_PPC||writes_)return fail(3);
        try{if(!B::write32(address,value))return fail(3);}
        catch(const std::exception&){return fail(3);}
        mail_.flags&=~H::IPC_PPC;mail_.pi_cause&=~H::PI_HOLLYWOOD;
        ++writes_;stage_=2;
        return boundary(c,authorized)||fail(3);
    }
    template<class C>bool finished(C& c,bool authorized)const{
        return stage_==2u&&boundary(c,authorized)&&!(mail_.flags&H::IPC_PPC)&&
            !(mail_.pi_cause&mail_.pi_mask)&&!(mail_.control&(M::X1|M::Y1|M::Y2));
    }
private:
    const void* cpu_=nullptr;const WakeReadyWitness* ready_=nullptr;
    ColdIpcSnapshot mail_{};std::array<uint32_t,8> words_{};
    uint32_t request_=0;uint64_t tick_=0;unsigned stage_=0,error_=0,reads_=0,writes_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool bad_alias(uint32_t a){return (a&0xc0000000u)==0x40000000u;}
    static bool reg(uint32_t a,uint32_t offset){return a==IosBus::IPC+offset||a==IosBus::MIRROR+offset;}
};
}
