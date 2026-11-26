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
    unsigned first_kind()const{return epoch_.first_kind();}
    unsigned failure()const{return error_;}
    unsigned writes()const{return writes_;}
    unsigned x2_writes()const{return x2_writes_;}
    unsigned write_detail()const{return write_detail_;}
    unsigned write_register()const{return write_register_;}
    unsigned write_control_bits()const{return write_control_bits_;}
    unsigned write_value_class()const{return write_value_class_;}
    template<class C>bool begin(C& c,const ReplyProcessorWitness& body,const WakeReadyWitness& ready,
                                const NestedWakeReturnWitness& nested,ExternalReturnWitness& frame,
                                uint32_t queue,uint32_t request,bool authorized){
        if(stage_||error_)return fail(1);
        epoch_=OpenTransactionEpoch(body.first_kind());
        const auto s=B::cold_snapshot();
        if(!epoch_held()||!authorized||!s||!nested.returned_at(c,ready,true)||
           !body.postwake_ready(c,frame,queue,request,true)||!ready.ready_held(c,true)||
           s->ppc!=request||s->arm!=request||s->steps!=epoch_.reply_steps()||s->queued||s->replies||s->event||
           (s->control&(M::X1|M::Y1|M::Y2|M::X2))||!(s->control&M::IY1)||!(s->control&M::IY2)||
           !(s->irq_mask&H::IPC_PPC)||!request||(request&31u))return fail(1);
        const bool pending=bool(s->flags&H::IPC_PPC);
        if((s->pi_cause&s->pi_mask)!=(pending?H::PI_HOLLYWOOD:0u)||
           bool(s->pi_cause&H::PI_HOLLYWOOD)!=pending)return fail(1);
        for(unsigned i=0;i<words_.size();++i){
            auto w=B::read_physical_word(request+4u*i);if(!w)return fail(1);words_[i]=*w;
        }
        if(words_[0]!=S::Reply||words_[1]!=epoch_.result_fd()||words_[2]!=S::Open)return fail(1);
        cpu_=&c;ready_=&ready;mail_=*s;request_=request;tick_=c.inst_count;
        stage_=pending?1u:2u;return true;
    }
    template<class C>unsigned boundary_class(C& c,bool authorized)const{
        if(!authorized||!stage_||stage_>3u||error_||cpu_!=&c||!ready_)return 1u;
        if(!ready_->ready_context_held(c,true))return 2u;
        auto s=B::cold_snapshot();
        if(!s)return 3u;
        if(!epoch_held()||!same_scheduler_ipc_snapshot(*s,mail_))return 4u;
        if(c.inst_count<tick_||c.inst_count-tick_>2048u)return 5u;
        for(unsigned i=0;i<words_.size();++i)if(B::read_physical_word(request_+4u*i)!=words_[i])return 6u;
        return 0u;
    }
    template<class C>bool boundary(C& c,bool authorized)const{return boundary_class(c,authorized)==0u;}
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
        const auto p=address&0x3fffffffu;
        write_register_=reg(p,M::PPCCTRL)?1u:reg(p,H::PPC_FLAG)?2u:reg(p,H::PPC_MASK)?3u:
            reg(p,M::PPCMSG)?4u:reg(p,M::ARMMSG)?5u:0u;
        // Report only public register classes and public control bits,
        // never the guest PC, address, pointer, or arbitrary operand.
        write_control_bits_=write_register_==1u?(value&0x3fu):0u;
        write_value_class_=value==H::IPC_PPC?1u:value==0u?2u:
            write_register_==1u&&value==mail_.control?3u:
            write_register_==1u&&value==(mail_.control|M::X2)?4u:
            write_register_==1u&&(value&~0x3fu)?5u:6u;
        // The owner V1302 trace observed a single X2 assertion after the
        // Hollywood latch was already cleared. Route it through the real
        // mailbox, with X1/Y1/Y2 absent and both enable bits unchanged.
        if(stage_==2u&&write_register_==1u){
            if(!boundary(c,authorized))return write_fail(2);
            if(bad_alias(address))return write_fail(3);
            if(value!=(mail_.control|M::X2)||x2_writes_||
               (mail_.control&(M::X1|M::Y1|M::Y2|M::X2)))return write_fail(5);
            try{if(!B::write32(address,value))return write_fail(7);}
            catch(const std::exception&){return write_fail(7);}
            mail_.control|=M::X2;++x2_writes_;stage_=3u;
            return boundary(c,authorized)||write_fail(8);
        }
        if(stage_!=1u)return write_fail(1);
        if(!boundary(c,authorized))return write_fail(2);
        if(bad_alias(address))return write_fail(3);
        if(write_register_!=2u)return write_fail(4);
        if(value!=H::IPC_PPC)return write_fail(5);
        if(writes_)return write_fail(6);
        try{if(!B::write32(address,value))return write_fail(7);}
        catch(const std::exception&){return write_fail(7);}
        mail_.flags&=~H::IPC_PPC;mail_.pi_cause&=~H::PI_HOLLYWOOD;
        ++writes_;stage_=2;
        return boundary(c,authorized)||write_fail(8);
    }
    template<class C>bool finished(C& c,bool authorized)const{
        return (stage_==2u||stage_==3u)&&boundary(c,authorized)&&!(mail_.flags&H::IPC_PPC)&&
            !(mail_.pi_cause&mail_.pi_mask)&&!(mail_.control&(M::X1|M::Y1|M::Y2));
    }
private:
    OpenTransactionEpoch epoch_{};
    bool epoch_held()const{return epoch_.valid()&&(!epoch_.second()||epoch_.acknowledged_descriptors(3u-epoch_.first_kind()));}
    const void* cpu_=nullptr;const WakeReadyWitness* ready_=nullptr;
    ColdIpcSnapshot mail_{};std::array<uint32_t,8> words_{};
    uint32_t request_=0;uint64_t tick_=0;unsigned stage_=0,error_=0,reads_=0,writes_=0,x2_writes_=0;
    unsigned write_detail_=0,write_register_=0,write_control_bits_=0,write_value_class_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool write_fail(unsigned n){if(!write_detail_)write_detail_=n;return fail(3);}
    static bool bad_alias(uint32_t a){return (a&0xc0000000u)==0x40000000u;}
    static bool reg(uint32_t a,uint32_t offset){return a==IosBus::IPC+offset||a==IosBus::MIRROR+offset;}
};
}
