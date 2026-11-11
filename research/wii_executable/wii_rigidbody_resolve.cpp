#include "wii_rigidbody_resolve.hpp"

#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {

std::uint32_t Add(std::uint32_t base, std::uint32_t offset) {
    if (!base || base > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii RigidBody state address");
    return base + offset;
}

WiiResolveResult Resolve(
    WiiMutableSnapshot& snapshot, std::uint32_t body, Vec3 incoming,
    const WiiDetach& detach, bool torque) {
    // Wii original ResolveForce__9RigidBodyFRCQ25UMath7Vector3:
    //    0x8030F570, length 0x8C.
    // Wii original ResolveTorque__9RigidBodyFRCQ25UMath7Vector3:
    //    0x8030F4E4, length 0x8C.
    // These bodies share the same sequence except target state vector.
    WiiMutableSnapshot next = snapshot;
    const auto initial = next.ReadOnly();
    const auto state = RigidBodyStateAddress(initial, body);

    // Original lbz + cmplwi == 2: the disabled/modeling state returns
    // without changing flags or performing the Detach call.
    if (initial.ReadU8(Add(state, 0x5D)) == 2)
        return WiiResolveResult::ignored_status_two;

    if (!detach)
        throw std::invalid_argument("Wii RigidBody::Detach callback required");

    // Both methods set status=0, OR flag 0x0040, THEN call Detach.
    // Do not assume Detach's virtual callbacks or world-space effects.
    next.WriteU8(Add(state, 0x5D), 0);
    next.WriteU16BE(Add(state, 0x1C),
        std::uint16_t(RigidBodyFlags(initial, body) | 0x0040u));
    detach(next, body);

    // Original PPC saves state pointer in r31 before calling Detach.
    // Read the post-callback accumulator at that SAME original address.
    const auto after = next.ReadOnly();
    const auto accumulator = Add(state, torque ? 0x60u : 0x50u);
    const Vec3 previous {
        ReadWiiF32(after, accumulator),
        ReadWiiF32(after, Add(accumulator, 4)),
        ReadWiiF32(after, Add(accumulator, 8))
    };
    const Vec3 updated {
        previous.x + incoming.x,
        previous.y + incoming.y,
        previous.z + incoming.z
    };
    next.WriteVec3BE(accumulator, updated);
    snapshot = std::move(next);
    return WiiResolveResult::accumulated;
}

} // namespace

WiiResolveResult WiiRigidBodyBaseResolveForce(
    WiiMutableSnapshot& snapshot, std::uint32_t body, Vec3 force,
    const WiiDetach& detach) {
    return Resolve(snapshot, body, force, detach, false);
}

WiiResolveResult WiiRigidBodyBaseResolveTorque(
    WiiMutableSnapshot& snapshot, std::uint32_t body, Vec3 torque,
    const WiiDetach& detach) {
    return Resolve(snapshot, body, torque, detach, true);
}

} // namespace undercover::vehicle
