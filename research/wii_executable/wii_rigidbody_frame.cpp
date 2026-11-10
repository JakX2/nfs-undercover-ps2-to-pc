#include "wii_rigidbody_frame.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>
#include <unordered_set>
#include <utility>

namespace undercover::vehicle {
namespace {
std::uint32_t Offset(std::uint32_t address, std::uint32_t delta) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - delta)
        throw std::out_of_range("invalid Wii frame state address");
    return address + delta;
}
constexpr std::size_t kMaxPrimitiveNodes = 4096;
} // namespace

WiiBeginFrameResult ApplyRigidBodyOnBeginFrame(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep,
    const WiiPrimitivePrepare& prepare) {
    // Original Wii OnBeginFrame at 0x8030EC44. Use an outer transaction:
    // private callbacks and V12 may write, but failed list traversal or
    // missing Wii memory may never partially alter the caller's snapshot.
    WiiMutableSnapshot next = snapshot;
    const auto original = next.ReadOnly();
    const std::uint32_t state = RigidBodyStateAddress(original, body);

    // 0x8030EC74..0x8030EC7C: state flags |= 0x0400.
    next.WriteU16BE(Offset(state, 0x1C),
                    std::uint16_t(RigidBodyFlags(original, body) | 0x0400u));
    const auto original_status = original.ReadU8(Offset(state, 0x5D));
    std::size_t prepared = 0;
    const bool should_integrate = (original_status != 2);

    if (should_integrate) {
        // 0x8030EC8C..0x8030ECAC: primitive intrusive list.
        // body+0x104 is the sentinel, its first word is the first node;
        // every node+0x00 contains the next link. The caller's callback
        // represents the original Prepare(Primitive*, State&).
        const std::uint32_t sentinel = Offset(body, 0x104);
        std::uint32_t node = next.ReadOnly().ReadU32BE(sentinel);
        std::unordered_set<std::uint32_t> visited;
        while (node != sentinel) {
            if (!node || (node & 3u) || prepared >= kMaxPrimitiveNodes ||
                !visited.insert(node).second)
                throw std::invalid_argument("invalid/cyclic Wii primitive list");
            if (!prepare)
                throw std::invalid_argument("primitive Prepare callback required");
            prepare(next, node, state);
            ++prepared;
            // Original loads the next pointer *after* the Prepare call.
            node = next.ReadOnly().ReadU32BE(node);
        }
        // 0x8030ECB0..ECB8: same timestep passed directly to DoIntegration.
        (void)ApplyDoIntegrationPostOrientationStage(next, body, timestep);
    }

    // 0x8030ECBC..0x8030ECD4: six zero words, force +0x50
    // and torque +0x60. This happens for all statuses, including 2.
    next.WriteVec3BE(Offset(state, 0x50), {0.f, 0.f, 0.f});
    next.WriteVec3BE(Offset(state, 0x60), {0.f, 0.f, 0.f});

    // 0x8030ECD8 onward: original RE-READS the state byte, since a
    // callback/integrator may have changed it, rather than using entry.
    const auto after = next.ReadOnly();
    const auto final_status = after.ReadU8(Offset(state, 0x5D));
    bool gravity_applied = false;
    if (final_status == 0) {
        const auto flags = RigidBodyFlags(after, body);
        // 0x8030ECE4..ECE8: snapshot current flags to state+0x1E.
        next.WriteU16BE(Offset(state, 0x1E), flags);
        if (flags & 0x0002u) {
            // 0x8030ECF8..0x8030ED0C: gravity is added AFTER force reset.
            // This is the force accumulator for the *next* integration,
            // not acceleration directly applied to velocity in this call.
            const float mass = RigidBodyMass(after, body);
            const float gravity = RigidBodyGravity(after, body);
            const float gravity_force = std::fma(mass, gravity, 0.f);
            next.WriteVec3BE(Offset(state, 0x50),
                             {0.f, gravity_force, 0.f});
            gravity_applied = true;
        }
    }
    snapshot = std::move(next);
    return {should_integrate, prepared, gravity_applied, final_status};
}

} // namespace undercover::vehicle
