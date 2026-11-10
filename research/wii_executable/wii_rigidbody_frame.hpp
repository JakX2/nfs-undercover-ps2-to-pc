#pragma once

#include "wii_rigidbody_final_transform.hpp"

#include <cstddef>
#include <cstdint>
#include <functional>

namespace undercover::vehicle {

// This callback is a HOST-SIDE placeholder for the original Wii
// RigidBody::Primitive::Prepare called once for each intrusive list node.
// It must be supplied for nonempty primitive lists; no gameplay behavior
// is invented for the unknown primitive implementation.
using WiiPrimitivePrepare = std::function<void(
    WiiMutableSnapshot& memory, std::uint32_t primitive_address,
    std::uint32_t state_address)>;

struct WiiBeginFrameResult {
    bool integration_called;
    std::size_t primitives_prepared;
    bool gravity_applied;
    std::uint8_t final_state_status;
};

// Reconstructs the direct-caller sequence from Wii OnBeginFrame__9RigidBodyFf
// (0x8030EC44, 240 bytes) using synthetic, private 32-bit Wii RAM snapshots.
// Invokes the tested V12 host integration only for state byte != 2.
// No simulator/process patching or original binary execution is performed.
WiiBeginFrameResult ApplyRigidBodyOnBeginFrame(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep,
    const WiiPrimitivePrepare& prepare = {});

} // namespace undercover::vehicle
