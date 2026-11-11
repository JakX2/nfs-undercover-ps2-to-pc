#pragma once

#include "wii_rigidbody_controls.hpp"

#include <cstdint>

namespace undercover::vehicle {

// Wii RigidBody base-vtable implementation of
// ShouldSleep__9RigidBodyCFv at 0x80315D18, 0xC4 bytes.
// The base vtable has this method in slot +0x3AC and the method's
// virtual call at +0x298 resolves to GetNumContactPoints in that base
// vtable. Derived classes can override either method, so this is NOT
// automatically an exact result for every real game rigid body.
//
// All reads are from bounded 32-bit big-endian synthetic/owner snapshots;
// host std::sqrt approximates PPC frsqrte refinement.
// Throws on unmapped Wii addresses rather than accessing a game process.
bool WiiRigidBodyBaseShouldSleep(const attrib::WiiAddressSpace& memory,
                                std::uint32_t rigid_body);

} // namespace undercover::vehicle
