#include "wii_rigidbody_sleep.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400;
constexpr std::uint32_t kEnvironment = kBody + 0x700;

void Put32(std::vector<std::uint8_t>& b, std::size_t off, std::uint32_t value) {
    assert(off + 4 <= b.size());
    b[off] = static_cast<std::uint8_t>(value >> 24);
    b[off + 1] = static_cast<std::uint8_t>(value >> 16);
    b[off + 2] = static_cast<std::uint8_t>(value >> 8);
    b[off + 3] = static_cast<std::uint8_t>(value);
}

void PutFloat(std::vector<std::uint8_t>& b, std::size_t off, float value) {
    std::uint32_t bits;
    static_assert(sizeof(bits) == sizeof(value), "IEEE float32 expected");
    std::memcpy(&bits, &value, sizeof(bits));
    Put32(b, off, bits);
}

WiiMutableSnapshot Fixture(std::uint8_t contacts=3, float radius=2.f,
                           float threshold=25.f, bool environment=true) {
    std::vector<std::uint8_t> raw(0x900, 0);
    Put32(raw, 0x70, kBody + 0x200);
    Put32(raw, 0x200, kState);
    Put32(raw, 0x78, environment ? kEnvironment : 0);
    raw[0x400 + 0x5C] = contacts;
    PutFloat(raw, 0x400 + 0x6C, radius);
    PutFloat(raw, 0x700 + 0xE0, threshold);
    WiiMutableSnapshot s({{kBody, std::move(raw)}});
    RigidBodySetLinearVelocity(s, kBody, {6.f, 8.f, 0.f}); // speed 10
    RigidBodySetAngularVelocity(s, kBody, {0.f, 3.f, 4.f}); // speed 5
    return s;
}
template<class Error, class F> void MustThrow(F fn) {
    bool caught = false;
    try { fn(); } catch (const Error&) { caught = true; }
    assert(caught);
}

void TestMotionThresholdStrictness() {
    // velocity length 10 + (angular length 5 * radius 2) = 20.
    auto s = Fixture(3, 2.f, 25.f);
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
    s = Fixture(3, 2.f, 20.f);
    assert(!WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody)); // strict <
    s = Fixture(3, 2.f, 19.f);
    assert(!WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
    s = Fixture(3, 1.f, 20.f);
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
}

void TestContactRequirement() {
    for (int count = 0; count <= 8; ++count) {
        auto s = Fixture(static_cast<std::uint8_t>(count));
        assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody) == (count > 2));
    }

    // Original GetNumContactPoints sign-extends the byte, but ShouldSleep
    // subsequently performs UNSIGNED cmplwi against 2.
    auto negative = Fixture(0xFF);
    assert(RigidBodyContactCount(negative.ReadOnly(), kBody) == -1);
    assert(WiiRigidBodyBaseShouldSleep(negative.ReadOnly(), kBody));
    negative = Fixture(0x80);
    assert(RigidBodyContactCount(negative.ReadOnly(), kBody) == -128);
    assert(WiiRigidBodyBaseShouldSleep(negative.ReadOnly(), kBody));
}

void TestZeroTinyAndSpecialCases() {
    auto s = Fixture(4, 0.f, .1f);
    RigidBodySetLinearVelocity(s, kBody, {0.f, 0.f, 0.f});
    RigidBodySetAngularVelocity(s, kBody, {0.f, 0.f, 0.f});
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));

    // Square of a 1e-6 component is smaller than Wii rsqrt threshold;
    // original sqrt helper therefore returns zero.
    RigidBodySetLinearVelocity(s, kBody, {0.000001f, 0.f, 0.f});
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));

    // Float NaN at comparison input produces no ordered less-than.
    s = Fixture(3, 2.f, std::numeric_limits<float>::quiet_NaN());
    assert(!WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
    s = Fixture(3, 2.f, 100.f);
    RigidBodySetLinearVelocity(s, kBody,
        {std::numeric_limits<float>::quiet_NaN(), 0.f, 0.f});
    // The original rsqrt helper returns zero for an unordered input,
    // so the linear contribution disappears rather than propagating NaN.
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
    s = Fixture(3, 2.f, std::numeric_limits<float>::infinity());
    assert(WiiRigidBodyBaseShouldSleep(s.ReadOnly(), kBody));
}

void TestUnmappedPointerFailsClosed() {
    const auto missing_environment = Fixture(3, 2.f, 25.f, false);
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseShouldSleep(missing_environment.ReadOnly(), kBody);
    });
    const auto s = Fixture();
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseShouldSleep(s.ReadOnly(), 0);
    });
}

void TestIndependentVelocityContributionsAndThresholdEdges() {
    // Distinguish linear-only and angular-only paths using synthetic vectors.
    auto linear = Fixture(3, 7.f, 10.f);
    RigidBodySetLinearVelocity(linear, kBody, {6.f, 8.f, 0.f});
    RigidBodySetAngularVelocity(linear, kBody, {0.f, 0.f, 0.f});
    assert(!WiiRigidBodyBaseShouldSleep(linear.ReadOnly(), kBody));
    linear.WriteF32BE(kEnvironment + 0xE0, 11.f);
    assert(WiiRigidBodyBaseShouldSleep(linear.ReadOnly(), kBody));

    auto angular = Fixture(3, 2.f, 10.f);
    RigidBodySetLinearVelocity(angular, kBody, {0.f, 0.f, 0.f});
    RigidBodySetAngularVelocity(angular, kBody, {0.f, 3.f, 4.f});
    assert(!WiiRigidBodyBaseShouldSleep(angular.ReadOnly(), kBody));
    angular.WriteF32BE(kEnvironment + 0xE0, 11.f);
    assert(WiiRigidBodyBaseShouldSleep(angular.ReadOnly(), kBody));

    // A zero radius must suppress angular motion, not linear motion.
    auto radius_zero = Fixture(3, 0.f, 1.f);
    RigidBodySetLinearVelocity(radius_zero, kBody, {0.f, 0.f, 0.f});
    assert(WiiRigidBodyBaseShouldSleep(radius_zero.ReadOnly(), kBody));
    RigidBodySetLinearVelocity(radius_zero, kBody, {6.f, 8.f, 0.f});
    assert(!WiiRigidBodyBaseShouldSleep(radius_zero.ReadOnly(), kBody));
}

} // namespace

int main() {
    TestMotionThresholdStrictness();
    TestContactRequirement();
    TestZeroTinyAndSpecialCases();
    TestUnmappedPointerFailsClosed();
    TestIndependentVelocityContributionsAndThresholdEdges();
}
