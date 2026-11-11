#pragma once

#include "wii_rigidbody_orientation.hpp"

#include <cstdint>

namespace undercover::vehicle {

// Original Wii base vtable +0x384 points to
// ConvertLocalToWorld__9RigidBodyCFRQ25UMath7Vector3b,
// at Wii 0x8030F1B4 (0xC8 bytes).
//
// Original transforms input vector IN PLACE, optionally adding the
// physics state's position when include_translation is true.
// This portable adaptation returns a value, never writes game RAM.
Vec3 WiiRigidBodyBaseConvertLocalToWorld(
    const attrib::WiiAddressSpace& snapshot,
    std::uint32_t rigid_body,
    Vec3 local,
    bool include_translation);

} // namespace undercover::vehicle
