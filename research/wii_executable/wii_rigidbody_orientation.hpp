#pragma once

#include "wii_rigidbody_controls.hpp"

#include <array>
#include <cstdint>

namespace undercover::vehicle {

struct WiiQuaternion {
    float x, y, z, w;
};
using WiiMatrix4 = std::array<float, 16>;

// Wii state object begins with XYZW quaternion at +0x00 and a 4x4
// matrix at +0x70. All data is BIG-ENDIAN Wii float32, not PC objects.
WiiQuaternion RigidBodyQuaternion(const attrib::WiiAddressSpace& memory,
                                 std::uint32_t body);
WiiMatrix4 RigidBodyOrientationMatrix(const attrib::WiiAddressSpace& memory,
                                     std::uint32_t body);

// Independently reconstructed Wii helper at 0x8023480C.
// Column/row convention is inherited from its explicit stores.
WiiMatrix4 WiiQuaternionToMatrix4(WiiQuaternion unit);

// V11 only: after the previous V10 clamping stage, update/normalize
// orientation quaternion and regenerate state+0x70 4x4 orientation matrix
// exactly when angular velocity square is nonzero (source branch).
// Stops immediately after the Wii VU0_quattom4 call at 0x8030FE70.
// Remaining DoIntegration transformations are NOT reconstructed.
// Deliberate safety adaptation: reject zero/nonfinite normalization inputs.
IntegrationPrefixPath ApplyDoIntegrationOrientationPrefix(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep);

} // namespace undercover::vehicle
