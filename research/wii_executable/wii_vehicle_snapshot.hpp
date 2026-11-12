#pragma once

#include "attrib_memory.hpp"

#include <cstdint>

namespace undercover::vehicle {

struct Vec3 {
    float x, y, z;
};

// Wii memory is read-only and always uses big-endian IEEE-754 f32 words.
float ReadWiiF32(const attrib::WiiAddressSpace& memory, std::uint32_t address);

// Wii RigidBody pointer chain: body +0x70 -> wrapper +0x00 -> state.
// Field offsets are evidence from original ELF, not portable object layout.
std::uint32_t RigidBodyStateAddress(const attrib::WiiAddressSpace& memory,
                                    std::uint32_t rigid_body);
Vec3 RigidBodyVelocity(const attrib::WiiAddressSpace& memory,
                       std::uint32_t rigid_body);
float RigidBodySpeed(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body);
float RigidBodySpeedXZ(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body);
float RigidBodyInverseMass(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body);
float RigidBodyRadius(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body);
std::uint8_t RigidBodyIndex(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body);
std::uint32_t RigidBodySimableType(const attrib::WiiAddressSpace& memory,
                                   std::uint32_t rigid_body);
float PVehicleSpeed(const attrib::WiiAddressSpace& memory, std::uint32_t vehicle);

// Numerical tail of Game_GetSimableSpeedKmh, not a vtable implementation.
// Original calls two virtual methods to find the physics component and speed;
// host caller supplies these conditions and the resulting raw speed directly.
float SimableSpeedKmh(bool simable_present, bool physics_present, float raw_speed);

}  // namespace undercover::vehicle
