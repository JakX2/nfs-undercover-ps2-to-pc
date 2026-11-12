#include "wii_vehicle_snapshot.hpp"

#include <cmath>
#include <cstring>
#include <limits>
#include <stdexcept>

namespace undercover::vehicle {
namespace {
std::uint32_t AddOffset(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii physics pointer");
    return address + offset;
}

// The Wii helper called 'rsqrt' at 0x80232544 returns an approximate
// *square root* for squared lengths greater than this original float constant.
// PowerPC frsqrte/Newton-Raphson refinements are NOT bit-matched on PC.
float ApproximateWiiLength(float squared) {
    constexpr float threshold = 5.00000006675716e-11f;
    if (!(squared > threshold)) return 0.0f;
    return std::sqrt(squared);
}
}  // namespace

float ReadWiiF32(const attrib::WiiAddressSpace& memory, std::uint32_t address) {
    static_assert(sizeof(float) == sizeof(std::uint32_t), "requires 32-bit float");
    const auto bits = memory.ReadU32BE(address);
    float value = 0.0f;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

std::uint32_t RigidBodyStateAddress(const attrib::WiiAddressSpace& memory,
                                    std::uint32_t rigid_body) {
    const auto wrapper = memory.ReadU32BE(AddOffset(rigid_body, 0x70));
    return memory.ReadU32BE(AddOffset(wrapper, 0));
}

Vec3 RigidBodyVelocity(const attrib::WiiAddressSpace& memory,
                       std::uint32_t rigid_body) {
    const auto state = RigidBodyStateAddress(memory, rigid_body);
    return {ReadWiiF32(memory, AddOffset(state, 0x20)),
            ReadWiiF32(memory, AddOffset(state, 0x24)),
            ReadWiiF32(memory, AddOffset(state, 0x28))};
}

float RigidBodySpeed(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body) {
    const auto v = RigidBodyVelocity(memory, rigid_body);
    return ApproximateWiiLength(std::fma(v.z, v.z,
                               std::fma(v.x, v.x, v.y * v.y)));
}

float RigidBodySpeedXZ(const attrib::WiiAddressSpace& memory, std::uint32_t rigid_body) {
    const auto v = RigidBodyVelocity(memory, rigid_body);
    return ApproximateWiiLength(std::fma(v.x, v.x, v.z * v.z));
}

float RigidBodyInverseMass(const attrib::WiiAddressSpace& memory,
                           std::uint32_t rigid_body) {
    return ReadWiiF32(memory, AddOffset(RigidBodyStateAddress(memory, rigid_body), 0x3C));
}

float RigidBodyRadius(const attrib::WiiAddressSpace& memory,
                      std::uint32_t rigid_body) {
    return ReadWiiF32(memory, AddOffset(RigidBodyStateAddress(memory, rigid_body), 0x6C));
}

std::uint8_t RigidBodyIndex(const attrib::WiiAddressSpace& memory,
                            std::uint32_t rigid_body) {
    return memory.ReadU8(AddOffset(RigidBodyStateAddress(memory, rigid_body), 0x5E));
}

std::uint32_t RigidBodySimableType(const attrib::WiiAddressSpace& memory,
                                   std::uint32_t rigid_body) {
    return memory.ReadU32BE(AddOffset(rigid_body, 0xFC));
}

float PVehicleSpeed(const attrib::WiiAddressSpace& memory, std::uint32_t vehicle) {
    return ReadWiiF32(memory, AddOffset(vehicle, 0x120));
}

float SimableSpeedKmh(bool simable_present, bool physics_present, float raw_speed) {
    if (!simable_present || !physics_present) return 0.0f;
    // Wii PPC: fmuls by 3600.0f, then fmuls by 0.001f.
    // Deliberately two f32 steps rather than a premultiplied 3.6f constant.
    return (raw_speed * 3600.0f) * 0.001f;
}

}  // namespace undercover::vehicle
