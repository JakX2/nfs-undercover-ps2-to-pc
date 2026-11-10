#pragma once

#include "wii_rigidbody_orientation.hpp"

#include <cstdint>

namespace undercover::vehicle {

// Independent host-side implementation of the post-orientation block
// 0x8030FE74..0x803100D4 in the owner's Wii PowerPC ELF.
// Models the scalar reciprocal choices, oriented inertia-like 4x4 matrix,
// and center-of-gravity position correction on a private Wii snapshot.
//
// As with V11, this is NOT an equivalent PPC ABI or a proven in-game
// simulation. Host C++ floating-point results may differ from Wii FPSCR.
// Copy-on-commit preserves the caller's snapshot on failed reads/writes.
IntegrationPrefixPath ApplyDoIntegrationPostOrientationStage(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep);

// Read back the Wii RigidBody's 16-float body-space transform at +0x84.
// It is used as the angular transform at the beginning of subsequent steps.
WiiMatrix4 RigidBodyBodyMatrix(const attrib::WiiAddressSpace& snapshot,
                               std::uint32_t body);

} // namespace undercover::vehicle
