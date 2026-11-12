#include "wii_rigidbody_sleep.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>

namespace undercover::vehicle {
namespace {
std::uint32_t Add(std::uint32_t base, std::uint32_t offset) {
    if (!base || base > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii ShouldSleep object address");
    return base + offset;
}

float ApproximatePpcSqrtForSpeed(Vec3 v) {
    // PPC sum order in original ShouldSleep: y*y + x*x + z*z.
    const float squared = std::fma(v.z, v.z,
                          std::fma(v.x, v.x, v.y * v.y));
    // Wii rsqrt__Ff at 0x80232544 returns approximate sqrt,
    // with original r2 constant bits 0x2E5BE6FF.
    constexpr float threshold = 5.00000006675716e-11f;
    if (!(squared > threshold)) return 0.f;
    return std::sqrt(squared);
}
} // namespace

bool WiiRigidBodyBaseShouldSleep(const attrib::WiiAddressSpace& m,
                                 std::uint32_t body) {
    // Wii ShouldSleep__9RigidBodyCFv 0x80315D18..0x80315DD8.
    const Vec3 angular = RigidBodyAngularVelocity(m, body);
    const float angular_speed = ApproximatePpcSqrtForSpeed(angular);
    const float linear_speed = RigidBodySpeed(m, body);
    const float radius = RigidBodyRadius(m, body);
    const auto environment = m.ReadU32BE(Add(body, 0x78));
    const float maximum_motion = ReadWiiF32(m, Add(environment, 0xE0));

    // 0x80315D84: fmadds radius*angular_speed + linear_speed.
    // 0x80315D8C..0x80315D90: ordered compare; only strictly
    // LESS than environment threshold executes the vtable call.
    const float motion = std::fma(radius, angular_speed, linear_speed);
    if (!(motion < maximum_motion))
        return false;

    // Base vtable +0x298 is GetNumContactPoints__9RigidBodyCFv
    // (0x8030100C). The original returns a SIGN-EXTENDED byte,
    // then checks it by UNSIGNED cmplwi >2 at 0x80315DA8.
    // Casting here preserves the original unsigned comparison even
    // for anomalous negative contact-byte values.
    return static_cast<std::uint32_t>(RigidBodyContactCount(m, body)) > 2u;
}

} // namespace undercover::vehicle
