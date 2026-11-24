#pragma once
#include "wii_native_ios_binding.h"
#include "wii_native_ios_boundary.h"
#include <array>
#include <cstddef>

namespace undercover::wii {
// Exclusive bounded AOT scheduling lane. The caller certifies exact resume
// PCs and must call poll instead of the legacy callback dispatcher. This
// deliberately does not implement nested IRQs, unrelated devices or HLE.
template<class Cpu,std::size_t N>
class NativeIosAotSession {
public:
    NativeIosAotSession(Cpu& cpu,NativeIosTransport& host,
                       const std::array<uint8_t,N>& vector)
        :cpu_(cpu),host_(host),vector_(vector),binding_(host){}
    NativeIosAotSession(const NativeIosAotSession&)=delete;
    NativeIosAotSession& operator=(const NativeIosAotSession&)=delete;
    bool poll(Cpu& cpu,bool certified){
        if(&cpu!=&cpu_)throw std::logic_error("native AOT session CPU mismatch");
        // This exclusive experiment must not hide a pending legacy event.
        if(cpu.pending_cb_count.load(std::memory_order_relaxed)||cpu.vblank_pending||
           cpu.dec_expired()||cpu.in_callback||cpu.dispatch_saved_ctx||cpu.ext_resched_pending)
            throw std::runtime_error("unsupported concurrent native AOT event");
        if(host_.active_pi_causes()&~HollywoodIrq::PI_HOLLYWOOD)
            throw std::runtime_error("unsupported concurrent native AOT PI source");
        if(in_flight_){
            if(certified&&cpu.pc==resume_pc_&&cpu.msr==resume_msr_){
                in_flight_=false;++returns_;
            }else{
                if(cpu.msr&IosBus::MSR_EE)
                    throw std::runtime_error("native AOT IRQ did not resume certified context");
                return false; // execute the already-entered guest handler
            }
        }
        if(!certified)return false;
        const auto result=service_native_ios_boundary(host_,cpu,vector_,true);
        using R=NativeBoundaryRoute;
        if(result.route==R::Unsafe||result.route==R::OtherPending||
           (result.enabled_pi&~HollywoodIrq::PI_HOLLYWOOD))
            throw std::runtime_error("unsupported native AOT boundary or PI source");
        if(result.route!=R::NativeEntered)return false;
        resume_pc_=cpu.srr0;resume_msr_=cpu.srr1;in_flight_=true;++entries_;
        return true;
    }
    unsigned entries() const noexcept{return entries_;}
    unsigned returns() const noexcept{return returns_;}
    bool in_flight() const noexcept{return in_flight_;}
private:
    Cpu& cpu_;
    NativeIosTransport& host_;
    const std::array<uint8_t,N> vector_;
    NativeIosBinding binding_;
    uint32_t resume_pc_=0u,resume_msr_=0u;
    unsigned entries_=0u,returns_=0u;
    bool in_flight_=false;
};
}
