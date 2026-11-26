#pragma once
#include "wii_native_ios_binding.h"
namespace undercover::wii {
// Read-only, explicit transaction epoch; never resets IOS, guest RAM,
// the mailbox or service counters. Epoch 0 is the first cold Open;
// 1/2 identifies the existing immediate/event descriptor of the next Open.
class OpenTransactionEpoch {
public:
    explicit constexpr OpenTransactionEpoch(unsigned first_kind=0):first_kind_(first_kind){}
    constexpr bool valid()const{return first_kind_<=2u;}
    constexpr bool second()const{return first_kind_!=0u;}
    constexpr unsigned first_kind()const{return first_kind_;}
    constexpr uint64_t steps()const{return second()?2u:0u;}
    constexpr uint64_t ack_steps()const{return steps()+1u;}
    constexpr uint64_t reply_steps()const{return steps()+2u;}
    constexpr uint32_t result_fd()const{return second()?1u:0u;}
    constexpr bool admits(unsigned kind)const{
        return valid()&&(kind==1u||kind==2u)&&(!second()||kind==3u-first_kind_);
    }
    bool descriptor_held()const{
        if(!valid())return false;
        if(!second())return true; // preserve the existing cold contract
        using D=StmIos::Device;
        if(!NativeIosBinding::is_open(0u,first_kind_==1u?D::Immediate:D::Event))return false;
        for(unsigned fd=1;fd<StmIos::DescriptorCount;++fd)
            for(auto d:{D::Immediate,D::Event,D::Fs,D::File,D::Es})
                if(NativeIosBinding::is_open(fd,d))return false;
        return true;
    }
    bool acknowledged_descriptors(unsigned kind)const{
        return acknowledged_descriptors(kind,[](unsigned fd,auto d){return NativeIosBinding::is_open(fd,d);});
    }
    template<class IsOpen>bool acknowledged_descriptors(unsigned kind,IsOpen is_open)const{
        using D=StmIos::Device;
        if(!admits(kind))return false;
        const auto next=kind==1u?D::Immediate:D::Event;
        if(!second())return is_open(0u,next);
        if(!is_open(0u,first_kind_==1u?D::Immediate:D::Event)||
           !is_open(1u,next))return false;
        for(unsigned fd=2;fd<StmIos::DescriptorCount;++fd)
            for(auto d:{D::Immediate,D::Event,D::Fs,D::File,D::Es})
                if(is_open(fd,d))return false;
        return true;
    }
    bool quiet(const ColdIpcSnapshot& s)const{
        using M=IpcMailbox;using H=HollywoodIrq;
        return valid()&&descriptor_held()&&!s.queued&&!s.replies&&!s.event&&s.steps==steps()&&
            (s.control&(M::IY1|M::IY2))&&!(s.control&(M::X1|M::Y1|M::Y2))&&
            !(s.flags&H::IPC_PPC)&&s.irq_mask==H::IPC_PPC&&
            (s.pi_mask&H::PI_HOLLYWOOD)&&!(s.pi_cause&s.pi_mask);
    }
private:
    unsigned first_kind_;
};
}
