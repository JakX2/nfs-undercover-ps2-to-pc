#pragma once

#include "wii_rigidbody_controls.hpp"

#include <cstdint>
#include <functional>

namespace undercover::vehicle {

// Original RigidBody base-vtable targets of DoDrag's +0x360/+0x364 slots.
// The original named Wii methods both call RigidBody::Detach, which can
// perform external virtual/object interactions not yet reconstructed.
// This callback MUST be supplied whenever the method takes the active path.
using WiiDetach = std::function<void(WiiMutableSnapshot&,
                                     std::uint32_t rigid_body)>;

enum class WiiResolveResult {
    ignored_status_two,
    accumulated
};

// Source-backed base method at Wii 0x8030F570. Adds force to state+0x50,
// wakes body to status=0 and ORs 0x0040 into the state flags before Detach.
// Returns ignored_status_two if state byte+0x5D==2.
WiiResolveResult WiiRigidBodyBaseResolveForce(
    WiiMutableSnapshot& snapshot, std::uint32_t body, Vec3 force,
    const WiiDetach& detach);

// Source-backed base method at Wii 0x8030F4E4. Same control path, but
// adds torque to state+0x60 instead of force.
WiiResolveResult WiiRigidBodyBaseResolveTorque(
    WiiMutableSnapshot& snapshot, std::uint32_t body, Vec3 torque,
    const WiiDetach& detach);

} // namespace undercover::vehicle
