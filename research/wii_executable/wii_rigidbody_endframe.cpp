#include "wii_rigidbody_endframe.hpp"

#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {
std::uint32_t Offset(std::uint32_t address, std::uint32_t field) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - field)
        throw std::out_of_range("invalid Wii OnEndFrame object address");
    return address + field;
}

void Require(bool present, const char* description) {
    if (!present)
        throw std::invalid_argument(description);
}
} // namespace

WiiEndFrameResult ApplyRigidBodyOnEndFrame(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep,
    bool collision_pass, const WiiEndFrameCallbacks& callbacks) {
    // Wii source: OnEndFrame__9RigidBodyFfb, 0x8030EA74, 0xF8 bytes.
    // Snapshot transactions are a deliberate host safety adaptation.
    WiiMutableSnapshot next = snapshot;
    const std::uint32_t state = RigidBodyStateAddress(next.ReadOnly(), body);
    const std::uint8_t status = next.ReadOnly().ReadU8(Offset(state, 0x5D));
    WiiEndFrameResult result{false, false, false, false, false, status, status, 0};

    if (status == 0) {
        if (collision_pass) {
            // 0x8030EAB4: UpdateCollider(body).
            Require(static_cast<bool>(callbacks.update_collider),
                    "missing original UpdateCollider host callback");
            callbacks.update_collider(next, body);
            result.collider_updated = true;

            // 0x8030EAB8..EAC0: clear bit 0x0004 AFTER collider update.
            const auto flags = RigidBodyFlags(next.ReadOnly(), body);
            next.WriteU16BE(Offset(state, 0x1C),
                            static_cast<std::uint16_t>(flags & ~0x0004u));

            // 0x8030EAC4..EACC: WCollider::IsEmpty at body +0xE0.
            const auto collider = next.ReadOnly().ReadU32BE(Offset(body, 0xE0));
            Require(collider != 0, "missing original WCollider object");
            Require(static_cast<bool>(callbacks.is_collider_empty),
                    "missing original WCollider::IsEmpty host callback");
            if (!callbacks.is_collider_empty(next, collider)) {
                // 0x8030EAD4..EAE0: original Wii .sdata2 constant
                // at r2-24524 is exactly 2.0f, using PPC fmuls.
                Require(static_cast<bool>(callbacks.world_collisions),
                        "missing original DoWorldCollisions host callback");
                callbacks.world_collisions(next, body, 2.0f * timestep);
                result.world_collisions_dispatched = true;
            }
        }

        // 0x8030EAE4: drag always runs in the active-status path.
        Require(static_cast<bool>(callbacks.do_drag),
                "missing original DoDrag host callback");
        callbacks.do_drag(next, body);
        result.drag_dispatched = true;

        // 0x8030EAEC..EB10: body virtual slot +0x3AC. Its return
        // value is tested against 0; if true, state status := 1.
        // It is NOT yet safe to name this virtual method "Sleep".
        Require(static_cast<bool>(callbacks.should_sleep),
                "missing Wii virtual +0x3AC host callback");
        if (callbacks.should_sleep(next, body)) {
            next.WriteU8(Offset(state, 0x5D), 1);
            result.entered_sleeping_state = true;
        }
    } else {
        // 0x8030EB14..EB3C. body+0x2C owns an interface whose
        // virtual slot +0x50 resolves a WWorldPos object.
        const auto manager = next.ReadOnly().ReadU32BE(Offset(body, 0x2C));
        Require(manager != 0, "missing Wii world position manager");
        Require(static_cast<bool>(callbacks.resolve_world_position),
                "missing Wii virtual +0x50 host callback");
        const auto world_position = callbacks.resolve_world_position(next, manager);
        Require(world_position != 0, "null Wii WWorldPos pointer");
        Require(static_cast<bool>(callbacks.sync_world_position),
                "missing Wii WWorldPos::Update host callback");
        // Original has fixed trailing arguments true, null, true.
        callbacks.sync_world_position(next, world_position,
                                      Offset(state, 0x10), Offset(body, 0xC4));
        result.world_position_synced = true;
    }

    // 0x8030EB40..EB48: always clear the original 0x0400
    // processing flag, preserving any other callback-modified flags.
    const auto flags = RigidBodyFlags(next.ReadOnly(), body);
    const auto cleared =
        static_cast<std::uint16_t>(flags & ~std::uint16_t(0x0400));
    next.WriteU16BE(Offset(state, 0x1C), cleared);
    result.exit_flags = cleared;
    result.exit_status = next.ReadOnly().ReadU8(Offset(state, 0x5D));
    snapshot = std::move(next);
    return result;
}

} // namespace undercover::vehicle
