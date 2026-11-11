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

// Wii base vtable +0x388: ConvertWorldToLocal at 0x8030F27C
// (0x1A0 bytes). The original removes position first if the
// boolean argument is true, transposes all 16 orientation words into
// stack memory, then multiplies the 3x3 rotation portion.
// Returns a value instead of overwriting the argument.
Vec3 WiiRigidBodyBaseConvertWorldToLocal(
    const attrib::WiiAddressSpace& snapshot,
    std::uint32_t rigid_body,
    Vec3 world,
    bool include_translation);

} // namespace undercover::vehicle
