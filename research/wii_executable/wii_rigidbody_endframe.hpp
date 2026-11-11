#pragma once

#include "wii_rigidbody_controls.hpp"

#include <cstdint>
#include <functional>

namespace undercover::vehicle {

// All functions below represent external, NOT-YET-DECOMPILED Wii
// interfaces. The provided host callbacks have no implied gameplay
// implementation. They operate on *private synthetic* Wii snapshots.
struct WiiEndFrameCallbacks {
    // Active status==0, collision_pass==true:
    std::function<void(WiiMutableSnapshot&, std::uint32_t body)> update_collider;
    std::function<bool(const WiiMutableSnapshot&, std::uint32_t collider)>
        is_collider_empty;
    std::function<void(WiiMutableSnapshot&, std::uint32_t body, float doubled_dt)>
        world_collisions;

    // Active status==0, regardless of collision_pass:
    std::function<void(WiiMutableSnapshot&, std::uint32_t body)> do_drag;
    std::function<bool(WiiMutableSnapshot&, std::uint32_t body)> should_sleep;

    // Inactive status !=0:
    std::function<std::uint32_t(WiiMutableSnapshot&, std::uint32_t manager)>
        resolve_world_position;
    // Original Update receives (state+0x10, body+0xC4, true,
    // NULL collider, true); those fixed original arguments are
    // documented but represented here by the two pointer fields.
    std::function<void(WiiMutableSnapshot&, std::uint32_t world_position,
                       std::uint32_t position_address,
                       std::uint32_t body_orientation_address)>
        sync_world_position;
};

struct WiiEndFrameResult {
    bool collider_updated;
    bool world_collisions_dispatched;
    bool drag_dispatched;
    bool entered_sleeping_state;
    bool world_position_synced;
    std::uint8_t entry_status;
    std::uint8_t exit_status;
    std::uint16_t exit_flags;
};

// Source-backed control flow from OnEndFrame__9RigidBodyFfb, Wii
// 0x8030EA74..0x8030EB68. The caller supplies opaque effects
// that cannot yet be reconstructed from this one function.
// Throws when an invoked callback is missing and leaves the
// caller-owned snapshot unchanged on ANY failure.
WiiEndFrameResult ApplyRigidBodyOnEndFrame(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep,
    bool collision_pass, const WiiEndFrameCallbacks& callbacks);

} // namespace undercover::vehicle
