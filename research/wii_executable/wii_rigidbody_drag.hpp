#pragma once

#include "wii_rigidbody_drag_gates.hpp"
#include "wii_rigidbody_resolve.hpp"
#include "wii_rigidbody_transform.hpp"

#include <cstdint>
#include <functional>

namespace undercover::vehicle {

// The four virtual calls inside Wii DoDrag are injected explicitly.
// The original base vtable targets are identified, but derived vehicle
// rigid bodies can override the methods at runtime.
struct WiiDragCallbacks {
    std::function<Vec3(WiiMutableSnapshot&, std::uint32_t, Vec3)> world_to_local;
    std::function<Vec3(WiiMutableSnapshot&, std::uint32_t, Vec3)> local_to_world;
    std::function<void(WiiMutableSnapshot&, std::uint32_t, Vec3)> resolve_torque;
    std::function<void(WiiMutableSnapshot&, std::uint32_t, Vec3)> resolve_force;
};

struct WiiDragResult {
    bool angular_path;
    bool linear_path;
    Vec3 world_torque;
    Vec3 world_force;
};

// Host adapter for the verified BASE-class vtable. ResolveForce/Torque
// need the separately supplied, still-opaque RigidBody::Detach callback.
// Do not use this to claim that derived vehicles share all base methods.
WiiDragCallbacks MakeWiiBaseDragCallbacks(const WiiDetach& detach);

// Original Wii DoDrag__9RigidBodyFv at 0x8030ED34, 0x480 bytes.
// The mathematical operations are reconstructed on synthetic/private
// bounded 32-bit big-endian Wii memory, using the virtual callbacks
// for world/local transforms and force/torque dispatch.
//
// Original semantics:
//  - initial bit 0x0002 -> return before either path;
//  - initial bit 0x0800 -> angular drag calculations and ResolveTorque;
//  - RE-READ flags after first callback; bit 0x0020 -> linear drag,
//    potentially changed by the first ResolveTorque's side effects.
//  - both conversions pass boolean false (no position translation).
//
// Host uses std::sqrt instead of PPC frsqrte approximation and is NOT
// verified bit-for-bit equivalent. All writes are copy-on-commit.
// Missing callback on a taken path throws, not silently skipped.
WiiDragResult ApplyRigidBodyDoDrag(
    WiiMutableSnapshot& snapshot, std::uint32_t body,
    const WiiDragCallbacks& callbacks);

} // namespace undercover::vehicle
