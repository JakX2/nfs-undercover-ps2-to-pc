#include "wii_rigidbody_orientation.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {

std::uint32_t AddWii(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii orientation address");
    return address + offset;
}

WiiQuaternion ReadQuaternion(const attrib::WiiAddressSpace& m,
                             std::uint32_t state) {
    return {ReadWiiF32(m, state), ReadWiiF32(m, AddWii(state, 4)),
            ReadWiiF32(m, AddWii(state, 8)), ReadWiiF32(m, AddWii(state, 12))};
}

WiiQuaternion IntegrateOrientation(WiiQuaternion q, Vec3 omega, float dt) {
    // Original Wii DoIntegration at 0x8030FD18..0x8030FE24.
    // Its angular velocity is already component-clamped by V10. The PPC
    // rotation is OMEGA * QUATERNION, not QUATERNION * OMEGA.
    const float x = omega.x * dt;
    const float y = omega.y * dt;
    const float z = omega.z * dt;
    const float dx = std::fma(x, q.w, std::fma(y, q.z, -(z * q.y)));
    const float dy = std::fma(y, q.w, std::fma(z, q.x, -(x * q.z)));
    const float dz = std::fma(z, q.w, std::fma(x, q.y, -(y * q.x)));
    const float dw = -std::fma(z, q.z, std::fma(y, q.y, x * q.x));
    q.x = std::fma(dx, 0.5f, q.x);
    q.y = std::fma(dy, 0.5f, q.y);
    q.z = std::fma(dz, 0.5f, q.z);
    q.w = std::fma(dw, 0.5f, q.w);

    // Wii original calls sqrt, divides 1 by its result, then scales all
    // quaternion components as float32 (0x8030FE28..0x8030FE6C).
    // The host uses a safe finite/positive check rather than propagating
    // a zero-length quaternion or invalid sqrt into the matrix writer.
    const float length_sq = std::fma(q.w, q.w,
                            std::fma(q.z, q.z,
                            std::fma(q.y, q.y, q.x * q.x)));
    if (!(length_sq > 0.f) || !std::isfinite(length_sq))
        throw std::domain_error("degenerate Wii orientation quaternion");
    const float inv = 1.f / std::sqrt(length_sq);
    q.x *= inv;
    q.y *= inv;
    q.z *= inv;
    q.w *= inv;
    if (!std::isfinite(q.x) || !std::isfinite(q.y) ||
        !std::isfinite(q.z) || !std::isfinite(q.w))
        throw std::domain_error("invalid normalized Wii quaternion");
    return q;
}

} // namespace

WiiQuaternion RigidBodyQuaternion(const attrib::WiiAddressSpace& m,
                                  std::uint32_t body) {
    return ReadQuaternion(m, RigidBodyStateAddress(m, body));
}

WiiMatrix4 RigidBodyOrientationMatrix(const attrib::WiiAddressSpace& m,
                                      std::uint32_t body) {
    const auto state = RigidBodyStateAddress(m, body);
    WiiMatrix4 matrix{};
    for (std::size_t i = 0; i < matrix.size(); ++i)
        matrix[i] = ReadWiiF32(m, AddWii(state, 0x70 + std::uint32_t(i * 4)));
    return matrix;
}

WiiMatrix4 WiiQuaternionToMatrix4(WiiQuaternion q) {
    // Exact index/sign layout of Wii VU0_quattom4 at 0x8023480C.
    // The original routine does NOT itself normalize the input.
    const float xx = 2.f * (q.x * q.x);
    const float yy = 2.f * (q.y * q.y);
    const float zz = 2.f * (q.z * q.z);
    const float xy = 2.f * (q.x * q.y);
    const float xz = 2.f * (q.x * q.z);
    const float yz = 2.f * (q.y * q.z);
    const float xw = 2.f * (q.x * q.w);
    const float yw = 2.f * (q.y * q.w);
    const float zw = 2.f * (q.z * q.w);
    return {
        1.f - (yy + zz), xy + zw, xz - yw, 0.f,
        xy - zw, 1.f - (xx + zz), yz + xw, 0.f,
        xz + yw, yz - xw, 1.f - (xx + yy), 0.f,
        0.f, 0.f, 0.f, 1.f
    };
}

IntegrationPrefixPath ApplyDoIntegrationOrientationPrefix(
    WiiMutableSnapshot& snapshot, std::uint32_t body, float timestep) {
    // Make a complete private copy so a failed quaternion/matrix write
    // cannot leave previous V10 position/velocity writes in the caller.
    WiiMutableSnapshot next = snapshot;
    const auto path = ApplyDoIntegrationClampedAngularPrefix(next, body, timestep);
    if (path == IntegrationPrefixPath::inactive_cleared) {
        snapshot = std::move(next);
        return path;
    }

    const auto m = next.ReadOnly();
    const auto state = RigidBodyStateAddress(m, body);
    const Vec3 omega = RigidBodyAngularVelocity(m, body);
    const float omega_sq = std::fma(omega.z, omega.z,
                           std::fma(omega.x, omega.x, omega.y * omega.y));

    // 0x8030FD10 fcmpu angular.lengthSquared with zero, equals -> skip.
    // The Wii then leaves both quaternion and orientation matrix unchanged.
    if (omega_sq == 0.f) {
        snapshot = std::move(next);
        return path;
    }

    const auto updated = IntegrateOrientation(ReadQuaternion(m, state),
                                              omega, timestep);
    const auto matrix = WiiQuaternionToMatrix4(updated);
    next.WriteVec4BE(state, {updated.x, updated.y, updated.z, updated.w});
    next.WriteMatrix4BE(AddWii(state, 0x70), matrix);
    snapshot = std::move(next);
    return path;
}

} // namespace undercover::vehicle
