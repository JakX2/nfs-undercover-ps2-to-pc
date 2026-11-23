#pragma once
#include "native_external_irq.h"
#include "wii_ios_bus.h"
#include <array>
#include <cstddef>
#include <cstdint>

// Y1-only external exception gating for an already-published native
// Broadway IOS reply. The installed original guest exception vector is
// verified by enter_external_irq. No guest handler, rfi, ACK, synthetic
// response, or host-side PowerPC execution is performed here.
//
// The caller must supply an actual next-not-yet-executed guest instruction
// boundary. It must also authenticate the original Wii guest candidate;
// this generic original-free hardware helper cannot verify game identity.
namespace undercover::wii {
template<class Context,size_t N>
ExternalEntry enter_queued_nand_y1(Context& cpu,IosBus& bus,
                                    const std::array<uint8_t,N>& installed,
                                    bool safe_guest_boundary){
    using M=IpcMailbox;
    using H=HollywoodIrq;
    const auto ctrl=bus.read32(IosBus::IPC+M::PPCCTRL);
    const auto flag=bus.read32(IosBus::IPC+H::PPC_FLAG);
    if(!ctrl||!flag||(*ctrl&M::Y1)==0u||(*ctrl&M::Y2)!=0u||
       (*flag&H::IPC_PPC)==0u||
       bus.pending_native_ios_request()||
       bus.services().queued_replies()!=0u){
        return ExternalEntry::NotPending;
    }
    return enter_external_irq(cpu,bus,installed,safe_guest_boundary);
}
}
