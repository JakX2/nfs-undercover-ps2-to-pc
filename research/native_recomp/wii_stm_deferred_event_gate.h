#pragma once
#include "wii_native_ios_binding.h"
#include <array>
#include <vector>

namespace undercover::wii {
// Device-side contract for the third startup transaction, after two completed
// STM opens. The caller must independently authenticate original guest code,
// the request's allocation, the service boundary and the ACK handler.
class StmDeferredEventGate {
public:
    using B=NativeIosBinding; using M=IpcMailbox; using H=HollywoodIrq; using S=StmIos;
    static constexpr uint32_t en=M::IY1|M::IY2;
    struct Arguments {uint32_t request,fd,input,input_size,output,output_size;};
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    bool begin(Arguments a,unsigned first_kind,bool authorized){
        auto s=B::cold_snapshot();
        if(stage_||error_||!authorized||!s||(first_kind!=1u&&first_kind!=2u))return fail(1);
        first_=first_kind; a_=a;
        if(!descriptors()||a.fd!=(first_==2u?0u:1u)||!a.request||(a.request&31u)||
           a.input_size>4096u||a.output_size<4u||a.output_size>4096u||
           !a.output||overlap(a.request,64u,a.output,a.output_size)||overlap(a.request,64u,a.input,a.input_size)||
           !range(a.request,64u)||!range(a.input,a.input_size)||!range(a.output,a.output_size)||
           s->steps!=4u||s->queued||s->replies||s->event||
           (s->control&(M::X1|M::Y1|M::Y2))||(s->control&en)!=en||
           s->irq_mask!=H::IPC_PPC||!(s->pi_mask&H::PI_HOLLYWOOD)||
           (s->flags&H::IPC_PPC)||(s->pi_cause&H::PI_HOLLYWOOD)||(s->pi_cause&s->pi_mask))return fail(1);
        for(unsigned i=0;i<16;++i){auto w=B::read_physical_word(a.request+4*i);if(!w)return fail(1);wire_[i]=*w;}
        if(wire_[0]!=S::Ioctl||wire_[2]!=a.fd||wire_[3]!=S::EventHook||
           wire_[4]!=a.input||wire_[5]!=a.input_size||wire_[6]!=a.output||wire_[7]!=a.output_size||
           !capture(a.input,a.input_size,input_)||!capture(a.output,a.output_size,output_))return fail(1);
        expected_=*s;stage_=1;return true;
    }
    // Read-only observation seams for native submit and IRQ continuations.
    bool submission_held(bool authorized)const{return stage_>=1u&&stage_<=3u&&boundary(authorized);}
    bool deferred_held(bool authorized)const{return stage_==4u&&boundary(authorized);}
    // The guest ACK handler owns the bus from the pending Y2 latch
    // through the subsequent Hollywood W1C. Reads must not pump IOS.
    bool ack_held(bool authorized)const{return stage_>=4u&&stage_<=6u&&boundary(authorized);}
    bool ack_latch_cleared(bool authorized)const{return (stage_==5u||stage_==6u)&&boundary(authorized);}
    std::optional<uint32_t> read_ack(uint32_t addr,uint32_t msr,bool authorized){
        if(!ack_held(authorized)||(msr&IosBus::MSR_EE)||
           (!reg(addr,M::PPCCTRL)&&!reg(addr,H::PPC_FLAG))){fail(6);return {};}
        const uint32_t expected=reg(addr,M::PPCCTRL)?expected_.control:expected_.flags;
        try{
            auto v=B::read32(addr);
            if(v&&*v==expected&&ack_held(authorized))return v;
        }catch(const std::exception&){}
        fail(6);return {};
    }
    std::optional<uint32_t> read_submission_control(uint32_t addr,uint32_t msr,bool authorized){
        if((stage_!=1u&&stage_!=2u)||(msr&IosBus::MSR_EE)||!reg(addr,M::PPCCTRL)||!boundary(authorized)){
            fail(5);return std::nullopt;
        }
        try{
            auto value=B::read32(addr);
            if(value&&*value==expected_.control&&boundary(authorized))return value;
        }catch(const std::exception&){}
        fail(5);return std::nullopt;
    }
    bool submit_write(uint32_t addr,uint32_t value,uint32_t msr,bool authorized){
        if(!boundary(authorized)||(msr&IosBus::MSR_EE)||(stage_!=1u&&stage_!=2u))return fail(2);
        if(stage_==1u){
            if(!reg(addr,M::PPCMSG)||value!=a_.request)return fail(2);
            expected_.ppc=value;
        }else{
            if(!reg(addr,M::PPCCTRL)||(value&~0x3fu)||!(value&M::X1)||(value&en)!=en)return fail(2);
            expected_.control=value&(M::X1|M::X2|en);expected_.queued=true;
        }
        if(!write(addr,value))return fail(2);
        ++stage_;return boundary(authorized)||fail(2);
    }
    bool accept(uint32_t msr,bool authorized){
        if(stage_!=3u||!boundary(authorized)||(msr&IosBus::MSR_EE))return fail(3);
        auto s=B::service_at_guest_boundary(msr);
        if(!s||s->progress!=S::Pump::Deferred||!s->broadway_irq_level||
           s->guest_exception_ready||s->serviced_steps!=5u)return fail(3);
        expected_.steps=5u;expected_.queued=false;expected_.event=true;
        expected_.control=(expected_.control&~M::X1)|M::Y2;
        expected_.flags|=H::IPC_PPC;expected_.pi_cause|=H::PI_HOLLYWOOD;
        stage_=4;return boundary(authorized)||fail(3);
    }
    bool ack_write(uint32_t addr,uint32_t value,uint32_t msr,bool authenticated_handler){
        if((stage_!=4u&&stage_!=5u)||!boundary(authenticated_handler)||(msr&IosBus::MSR_EE))return fail(4);
        if(stage_==4u){
            if(!reg(addr,M::PPCCTRL)||value!=expected_.control)return fail(4);
            expected_.control&=~M::Y2;
        }else{
            if(!reg(addr,H::PPC_FLAG)||value!=H::IPC_PPC)return fail(4);
            expected_.flags&=~H::IPC_PPC;expected_.pi_cause&=~H::PI_HOLLYWOOD;
        }
        if(!write(addr,value))return fail(4);
        ++stage_;return boundary(authenticated_handler)||fail(4);
    }
    bool completed(bool authorized)const{return stage_==6u&&boundary(authorized);}
private:
    Arguments a_{};unsigned first_=0,stage_=0,error_=0;
    ColdIpcSnapshot expected_{};
    std::array<uint32_t,16> wire_{};
    std::vector<uint8_t> input_,output_;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(uint32_t a,uint32_t n,uint32_t b,uint32_t m){
        return n&&m&&uint64_t(a)<uint64_t(b)+m&&uint64_t(b)<uint64_t(a)+n;
    }
    static bool range(uint32_t a,uint32_t n){
        return !n||(a&&uint64_t(a)+n<=0x100000000ull&&B::read_physical_byte(a)&&B::read_physical_byte(a+n-1u));
    }
    static bool capture(uint32_t a,uint32_t n,std::vector<uint8_t>& out){
        out.clear();out.reserve(n);
        for(uint32_t i=0;i<n;++i){auto v=B::read_physical_byte(a+i);if(!v)return false;out.push_back(*v);}return true;
    }
    static bool unchanged(uint32_t a,const std::vector<uint8_t>& bytes){
        for(size_t i=0;i<bytes.size();++i){if(B::read_physical_byte(a+uint32_t(i))!=bytes[i])return false;}return true;
    }
    bool descriptors()const{
        auto d=first_==2u?S::Device::Event:S::Device::Immediate;
        auto e=first_==2u?S::Device::Immediate:S::Device::Event;
        return B::is_open(0u,d)&&B::is_open(1u,e);
    }
    static bool reg(uint32_t a,uint32_t off){
        if((a&0xc0000000u)==0x40000000u)return false;
        a&=0x3fffffffu;return a==IosBus::IPC+off||a==IosBus::MIRROR+off;
    }
    static bool write(uint32_t a,uint32_t v){
        try{return B::write32(a,v);}catch(const std::exception&){return false;}
    }
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
           a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&a.steps==b.steps&&
           a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    bool boundary(bool authorized)const{
        auto s=B::cold_snapshot();
        if(!authorized||error_||!stage_||!s||!same(*s,expected_)||!descriptors())return false;
        for(unsigned i=0;i<16;++i)if(B::read_physical_word(a_.request+4*i)!=wire_[i])return false;
        return unchanged(a_.input,input_)&&unchanged(a_.output,output_);
    }
};
}
