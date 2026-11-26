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
