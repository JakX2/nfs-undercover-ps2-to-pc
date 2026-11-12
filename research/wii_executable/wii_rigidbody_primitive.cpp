#include "wii_rigidbody_primitive.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>

namespace undercover::vehicle {
namespace {

std::uint32_t Add(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii primitive/state address");
    return address + offset;
}

Vec3 ReadVec(const attrib::WiiAddressSpace& memory,
             std::uint32_t address) {
    return {
        ReadWiiF32(memory, address),
        ReadWiiF32(memory, Add(address, 4)),
        ReadWiiF32(memory, Add(address, 8))
    };
}

} // namespace

Vec3 WiiPrimitiveLocalPosition(const attrib::WiiAddressSpace& memory,
                               std::uint32_t primitive_address) {
    return ReadVec(memory, Add(primitive_address, 0x28));
}

Vec3 WiiPrimitivePreparedWorldPosition(const attrib::WiiAddressSpace& memory,
                                       std::uint32_t primitive_address) {
    return ReadVec(memory, Add(primitive_address, 0x38));
}

void WiiRigidBodyPrimitivePrepare(
    WiiMutableSnapshot& snapshot, std::uint32_t primitive_address,
    std::uint32_t state_address) {
    // Original Wii PPC Prepare at 0x8030BCB4..0x8030BD58:
    // lwz primitive+0x28,+0x2C,+0x30 into stack, then lfs float32.
    // The orientation comes directly from the STATE argument r4.
    // The state pointer must not be inferred by following a body pointer.
    const auto view = snapshot.ReadOnly();
    const Vec3 local = WiiPrimitiveLocalPosition(view, primitive_address);

    const float m00 = ReadWiiF32(view, Add(state_address, 0x70));
    const float m01 = ReadWiiF32(view, Add(state_address, 0x74));
    const float m02 = ReadWiiF32(view, Add(state_address, 0x78));
    const float m10 = ReadWiiF32(view, Add(state_address, 0x80));
    const float m11 = ReadWiiF32(view, Add(state_address, 0x84));
    const float m12 = ReadWiiF32(view, Add(state_address, 0x88));
    const float m20 = ReadWiiF32(view, Add(state_address, 0x90));
    const float m21 = ReadWiiF32(view, Add(state_address, 0x94));
    const float m22 = ReadWiiF32(view, Add(state_address, 0x98));

    // Match the original f32 instruction dependency order:
    // f = (y * matrix-row1); f = fmadds(x, row0, f);
    // f = fmadds(z, row2, f); frsp(f); fadds(f, state-position).
    // std::fma is a host approximation, not a proven Wii bitwise match.
    const float x = std::fma(local.z, m20,
                    std::fma(local.x, m00, local.y * m10));
    const float y = std::fma(local.z, m21,
                    std::fma(local.x, m01, local.y * m11));
    const float z = std::fma(local.z, m22,
                    std::fma(local.x, m02, local.y * m12));
    const Vec3 position = ReadVec(view, Add(state_address, 0x10));

    // Original writes three float32 values at primitive+0x38/+0x3C/+0x40.
    // Host snapshot WriteVec3BE rejects incomplete/unmapped output atomically.
    snapshot.WriteVec3BE(Add(primitive_address, 0x38),
                         {x + position.x, y + position.y, z + position.z});
}

WiiPrimitivePrepare MakeWiiPrimitivePrepareCallback() {
    return [](WiiMutableSnapshot& memory, std::uint32_t primitive,
              std::uint32_t state) {
        WiiRigidBodyPrimitivePrepare(memory, primitive, state);
    };
}

} // namespace undercover::vehicle
