#pragma once
#include "wii_ios_yield_scheduler.h"
#include <optional>

// At an authenticated original guest scheduling boundary, service exactly
// one native IOS completion only after Broadway's Y2 and Hollywood W1C.
// No synthetic request, status, handler, guest context, or timing is created.
// The caller must authenticate that boundary; this helper owns no PC policy.
namespace undercover::wii {
inline std::optional<IosYieldState> service_deferred_reply_at_guest_boundary(
    IosBus& bus,uint32_t guest_msr){
    using M=IpcMailbox;
    using H=HollywoodIrq;
    if(bus.pending_native_ios_request()||
       bus.services().queued_replies()==0u)return std::nullopt;
    const auto ctrl=bus.read32(IosBus::IPC+M::PPCCTRL);
    const auto flag=bus.read32(IosBus::IPC+H::PPC_FLAG);
    if(!ctrl||!flag||(*ctrl&(M::Y1|M::Y2))!=0u||
       (*flag&H::IPC_PPC)!=0u||bus.external_irq_level())
        return std::nullopt;
    IosYieldScheduler scheduler(bus);
    return scheduler.service_one(guest_msr);
}
}
