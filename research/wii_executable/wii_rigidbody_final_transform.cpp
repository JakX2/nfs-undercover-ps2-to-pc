#include "wii_rigidbody_final_transform.hpp"

#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {

std::uint32_t Add(std::uint32_t base, std::uint32_t delta) {
    if (!base || base > std::numeric_limits<std::uint32_t>::max() - delta)
        throw std::out_of_range("invalid Wii rigid-body matrix address");
    return base + delta;
}

WiiMatrix4 ReadMatrix4(const attrib::WiiAddressSpace& m,
                       std::uint32_t start) {
    WiiMatrix4 result{};
    for (std::size_t i = 0; i < 16; ++i)
        result[i] = ReadWiiF32(m, Add(start, std::uint32_t(i * 4)));
    return result;
}

WiiMatrix4 Transpose(const WiiMatrix4& source) {
    WiiMatrix4 result{};
    for (std::size_t row = 0; row < 4; ++row)
        for (std::size_t column = 0; column < 4; ++column)
            result[row * 4 + column] = source[column * 4 + row];
    return result;
}

WiiMatrix4 Multiply(const WiiMatrix4& a, const WiiMatrix4& b) {
    // VU0_MATRIX4_mult, Wii 0x802348FC, loops rows/columns with an
    // initial row[1]*column[1], followed by FMAs for indices 0,2,3.
    WiiMatrix4 result{};
    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = 0; column < 4; ++column) {
            float value = a[row * 4 + 1] * b[4 + column];
            value = std::fma(a[row * 4], b[column], value);
            value = std::fma(a[row * 4 + 2], b[8 + column], value);
            value = std::fma(a[row * 4 + 3], b[12 + column], value);
            result[row * 4 + column] = value;
        }
    }
    return result;
}

Vec3 RotatedCenter(const WiiMatrix4& rotation, Vec3 center) {
    // DoIntegration 0x8030FA7C..0x8030FAE8 and 0x80310000..0x8031008C.
    // These explicitly use the columns of the state orientation matrix,
    // with the original terms initialized in the Y, X, Z order.
    return {
        std::fma(center.z, rotation[8],
                 std::fma(center.x, rotation[0], center.y * rotation[4])),
        std::fma(center.z, rotation[9],
                 std::fma(center.x, rotation[1], center.y * rotation[5])),
        std::fma(center.z, rotation[10],
                 std::fma(center.x, rotation[2], center.y * rotation[6]))
    };
}

float ReciprocalIfAboveThreshold(float raw) {
    // Wii 0x8030FE74..0x8030FEBC compares using fcmpo GT. The original
    // r2-24532 constant has f32 bits 0x358637BD (approximately 1e-6).
    // Zero, negative, too-small and NaN values are NOT reciprocated.
    constexpr float threshold = 0.000001f;
    return raw > threshold ? (1.f / raw) : raw;
}

} // namespace

WiiMatrix4 RigidBodyBodyMatrix(const attrib::WiiAddressSpace& m,
                               std::uint32_t body) {
    return ReadMatrix4(m, Add(body, 0x84));
}

IntegrationPrefixPath ApplyDoIntegrationPostOrientationStage(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep) {
    WiiMutableSnapshot next = snapshot;
    const auto before = next.ReadOnly();
    const auto state = RigidBodyStateAddress(before, body);
    if (before.ReadU8(Add(state, 0x5D)) != 0) {
        // Original returns before doing any center-of-gravity/matrix work.
        const auto path = ApplyDoIntegrationOrientationPrefix(next, body, timestep);
        snapshot = std::move(next);
        return path;
    }

    const Vec3 center = RigidBodyCenterOfGravity(before, body);
    const WiiMatrix4 old_rotation =
        RigidBodyOrientationMatrix(before, body);
    const Vec3 old_rotated_center = RotatedCenter(old_rotation, center);

    const auto path = ApplyDoIntegrationOrientationPrefix(next, body, timestep);
    const auto active = next.ReadOnly();
    const auto updated_state = RigidBodyStateAddress(active, body);

    // Matrix D: body+0x84..+0xC0 is replaced with a diagonal 4x4.
    // Entries originate from state+0x40,+0x44,+0x48; only values
    // strictly greater than the original threshold are reciprocated.
    const float dx = ReciprocalIfAboveThreshold(
        ReadWiiF32(active, Add(updated_state, 0x40)));
    const float dy = ReciprocalIfAboveThreshold(
        ReadWiiF32(active, Add(updated_state, 0x44)));
    const float dz = ReciprocalIfAboveThreshold(
        ReadWiiF32(active, Add(updated_state, 0x48)));
    const WiiMatrix4 diagonal{
        dx,0.f,0.f,0.f,
        0.f,dy,0.f,0.f,
        0.f,0.f,dz,0.f,
        0.f,0.f,0.f,1.f
    };

    const WiiMatrix4 rotation = RigidBodyOrientationMatrix(active, body);
    // The original transposes the rotated state matrix into a stack temp
    // before making two VU0_MATRIX4_mult calls:
    //   temp = D * R;    result = transpose(R) * temp.
    const WiiMatrix4 first = Multiply(diagonal, rotation);
    const WiiMatrix4 transformed = Multiply(Transpose(rotation), first);
    next.WriteMatrix4BE(Add(body, 0x84), transformed);

    // Final 0x80310000..0x803100D4: keep the original center-of-gravity
    // point fixed as orientation changes, correcting state position by
    // (old world center offset - updated world center offset).
    const Vec3 new_rotated_center = RotatedCenter(rotation, center);
    const Vec3 position = RigidBodyPosition(active, body);
    const Vec3 corrected{
        position.x + (old_rotated_center.x - new_rotated_center.x),
        position.y + (old_rotated_center.y - new_rotated_center.y),
        position.z + (old_rotated_center.z - new_rotated_center.z)
    };
    next.WriteVec3BE(Add(updated_state, 0x10), corrected);

    snapshot = std::move(next);
    return path;
}

} // namespace undercover::vehicle
