#pragma once

#include "wii_rigidbody_frame.hpp"

#include <cstdint>

namespace undercover::vehicle {

// Original Wii Prepare__Q29RigidBody9PrimitiveFRCQ29RigidBody5State,
// 0x8030BCB4, 0xA8 bytes. It reads the primitive's three local float32
// values at +0x28/+0x2C/+0x30, transforms them through the source state
// rotation+translation, and writes the three world float32 components
// to primitive +0x38/+0x3C/+0x40.
//
// Both addresses are original 32-bit Wii virtual addresses in a bounded
// synthetic/owner-local memory snapshot, never native host pointers.
// Host FMA behavior is approximate, not bit-accurate Wii FPSCR emulation.
void WiiRigidBodyPrimitivePrepare(
    WiiMutableSnapshot& snapshot, std::uint32_t primitive_address,
    std::uint32_t state_address);

// Source-backed implementation of the primitive callback supplied to
// ApplyRigidBodyOnBeginFrame. No external Wii game method is called.
WiiPrimitivePrepare MakeWiiPrimitivePrepareCallback();

// Read-only helpers for the original primitive fields.
Vec3 WiiPrimitiveLocalPosition(const attrib::WiiAddressSpace& memory,
                               std::uint32_t primitive_address);
Vec3 WiiPrimitivePreparedWorldPosition(const attrib::WiiAddressSpace& memory,
                                       std::uint32_t primitive_address);

} // namespace undercover::vehicle
