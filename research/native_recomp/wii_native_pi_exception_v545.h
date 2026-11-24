#pragma once
#include "native_external_irq.h"
#include "wii_native_ios_transport.h"
namespace undercover::wii {
// Expose all synchronized, enabled PI causes to the exception-entry code.
// A bounded caller must explicitly authorize the devices for which its
// original handler route is ready. Never silently discard an enabled source.
class NativePiExceptionSource {
public:
    NativePiExceptionSource(NativeIosTransport& transport,uint32_t allowed)
        :transport_(transport),allowed_(allowed){
        if(!allowed_)throw std::invalid_argument("empty native PI exception ownership");
    }
    bool external_exception_pending(uint32_t msr)const{
        if(!(msr&IosBus::MSR_EE))return false;
        const auto active=transport_.active_pi_causes();
        if(active&~allowed_)throw std::runtime_error("unowned active native PI interrupt");
        return active!=0;
    }
private:
    NativeIosTransport& transport_;
    uint32_t allowed_;
};
template<class Context,size_t N>
ExternalEntry enter_native_pi_irq(Context& cpu,NativeIosTransport& transport,
    const std::array<uint8_t,N>& installed,uint32_t allowed,bool safe_boundary){
    NativePiExceptionSource source(transport,allowed);
    return enter_external_irq(cpu,source,installed,safe_boundary);
}
}
