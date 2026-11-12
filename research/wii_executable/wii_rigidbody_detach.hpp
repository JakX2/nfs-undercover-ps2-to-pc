#pragma once

#include "wii_rigidbody_controls.hpp"

#include <cstdint>
#include <functional>

namespace undercover::vehicle {

// External virtual targets reached by Wii RigidBody::Detach.
// The original owner and linked-object virtual implementations have
// NOT yet been reconstructed; do not replace them with guessed effects.
struct WiiDetachCallbacks {
    // Original virtual slot +0x7C on the owner at body+0x2C.
    std::function<std::uint32_t(WiiMutableSnapshot&, std::uint32_t owner)>
        resolve_linked_object;
    // Original Sim::GetTime__3SimFv at 0x80378E60; return value unused
    // by this caller, but its ordering and possible side effects matter.
    std::function<void(WiiMutableSnapshot&)> sim_get_time;
    // Original virtual +0x3C on the returned linked object.
    // The last arguments are (source_constant=0xC91B90D9, 0, 2).
    std::function<void(WiiMutableSnapshot&, std::uint32_t linked_object,
                       std::uint32_t source_constant,
                       std::uint32_t arg5, std::uint32_t arg6)>
        dispatch_linked_event;
};

struct WiiDetachResult {
    bool cleared_attached_flag;
    bool event_sent;
    std::uint32_t owner;
    std::uint32_t linked_object;
};

// Source-backed base RigidBody::Detach at 0x8030E46C (160 bytes).
// Returns immediately when state flag 0x0002 is absent. Otherwise,
// clears that flag, obtains owner through the original BASE GetOwner
// vtable method (body+0x2C), resolves an optional linked object, calls
// Sim::GetTime and dispatches an event if the linked object exists.
//
// Required callbacks fail closed when their original path is taken.
// Operates only on host-owned, bounded Wii snapshots and commits
// atomically on success, not on a running Wii or patched retail binary.
WiiDetachResult WiiRigidBodyBaseDetach(
    WiiMutableSnapshot& snapshot, std::uint32_t body,
    const WiiDetachCallbacks& callbacks);

} // namespace undercover::vehicle
