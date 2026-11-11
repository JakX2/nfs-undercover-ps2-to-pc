#include "wii_rigidbody_controls.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

using namespace undercover::vehicle;
using undercover::attrib::WiiAddressSpace;
using undercover::attrib::WiiMemoryRegion;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;

void Put32(std::vector<std::uint8_t>& b, std::size_t off, std::uint32_t v) {
    assert(off + 4 <= b.size());
    b[off] = std::uint8_t(v >> 24);
    b[off+1] = std::uint8_t(v >> 16);
    b[off+2] = std::uint8_t(v >> 8);
    b[off+3] = std::uint8_t(v);
}

void PutF32(std::vector<std::uint8_t>& b, std::size_t off, float v) {
    std::uint32_t bits = 0;
    std::memcpy(&bits, &v, 4);
    Put32(b, off, bits);
}

WiiMutableSnapshot Fixture(std::uint16_t flags=0x1004, std::uint8_t contacts=3,
                           std::uint8_t status=1) {
    std::vector<std::uint8_t> raw(0x900, 0);
    Put32(raw, 0x70, kBody+0x200); // wrapper
    Put32(raw, 0x200, kState); // state
    Put32(raw, 0x78, kBody+0x700); // gravity object
    raw[0x400+0x1c] = std::uint8_t(flags >> 8);
    raw[0x400+0x1d] = std::uint8_t(flags);
    raw[0x400+0x5c] = contacts;
    raw[0x400+0x5d] = status;
    PutF32(raw, 0x400+0x2c, 1600.0f); // mass
    PutF32(raw, 0x700+0xf0, -9.81f); // gravity field
    PutF32(raw, 0xe4, 1.25f);
    PutF32(raw, 0xe8, 2.5f);
    PutF32(raw, 0xec, 3.75f);
    return WiiMutableSnapshot({{kBody, std::move(raw)}});
}

template <class E, class F> void MustThrow(F f) {
    bool threw = false;
    try { f(); } catch (const E&) { threw = true; }
    assert(threw);
}

bool Equal(Vec3 a, Vec3 b) {
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

void TestFlags() {
    auto s = Fixture();
    auto m = s.ReadOnly();
    assert(RigidBodyFlags(m, kBody) == 0x1004);
    assert(!RigidBodyIsAnchored(m, kBody));
    assert(RigidBodyHadPassiveCollision(m, kBody));
    assert(RigidBodyHadWorldCollision(m, kBody));
    assert(RigidBodyHadCollision(m, kBody));
    assert(RigidBodyContactCount(m, kBody) == 3);
    assert(RigidBodyIsInGroundContact(m, kBody));
    assert(RigidBodyIsSleeping(m, kBody));
    assert(RigidBodyIsModeling(m, kBody)); // original code: status != 2
    assert(RigidBodyMass(m, kBody) == 1600.0f);
    assert(std::abs(RigidBodyGravity(m, kBody) + 9.81f) < 0.0001f);
    assert(Equal(RigidBodyCenterOfGravity(m, kBody), {1.25f, 2.5f, 3.75f}));

    RigidBodySetAnchored(s, kBody, true);
    m = s.ReadOnly();
    assert(RigidBodyFlags(m, kBody) == 0x1084);
    assert(RigidBodyIsAnchored(m, kBody));
    RigidBodySetAnchored(s, kBody, true); // idempotence
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x1084);
    RigidBodySetAnchored(s, kBody, false);
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x1004);

    auto bit3 = Fixture(0x0008, 0, 2);
    const auto n = bit3.ReadOnly();
    assert(RigidBodyHadCollision(n, kBody));
    assert(!RigidBodyHadWorldCollision(n, kBody));
    assert(!RigidBodyHadPassiveCollision(n, kBody));
    assert(!RigidBodyIsAnchored(n, kBody));
    assert(!RigidBodyIsSleeping(n, kBody));
    assert(!RigidBodyIsModeling(n, kBody));
    assert(RigidBodyContactCount(n, kBody) == 0);
    assert(!RigidBodyIsInGroundContact(n, kBody));

    auto minus_one = Fixture(0, 0xff, 3);
    assert(RigidBodyContactCount(minus_one.ReadOnly(), kBody) == -1);
    assert(RigidBodyIsInGroundContact(minus_one.ReadOnly(), kBody));
    auto minus_128 = Fixture(0, 0x80, 0);
    assert(RigidBodyContactCount(minus_128.ReadOnly(), kBody) == -128);
}

void TestForces() {
    auto s = Fixture();
    const auto original = s.ReadOnly();
    assert(Equal(RigidBodyForce(original, kBody), {0, 0, 0}));
    assert(Equal(RigidBodyTorque(original, kBody), {0, 0, 0}));
    RigidBodySetForce(s, kBody, {1.5f, -2.5f, 100.0f});
    RigidBodySetTorque(s, kBody, {-3.f, 4.f, 0.25f});
    auto m = s.ReadOnly();
    assert(Equal(RigidBodyForce(m, kBody), {1.5f, -2.5f, 100.f}));
    assert(Equal(RigidBodyTorque(m, kBody), {-3.f, 4.f, 0.25f}));
    assert(m.ReadU32BE(kState + 0x50) == 0x3FC00000u); // 1.5f big endian
    assert(m.ReadU32BE(kState + 0x54) == 0xC0200000u); // -2.5f
    assert(RigidBodyMass(m, kBody) == 1600.f);
    assert(RigidBodyFlags(m, kBody) == 0x1004); // unrelated flags preserved

    RigidBodySetCenterOfGravity(s, kBody, {-1.f, 0.f, 7.5f});
    m = s.ReadOnly();
    assert(Equal(RigidBodyCenterOfGravity(m, kBody), {-1.f, 0.f, 7.5f}));
    assert(Equal(RigidBodyForce(m, kBody), {1.5f, -2.5f, 100.f}));
    assert(m.ReadU32BE(kBody+0xe4) == 0xBF800000u);
    assert(m.ReadU32BE(kBody+0xe8) == 0);
    assert(m.ReadU32BE(kBody+0xec) == 0x40F00000u);
}

void TestRejectedWritesAreAtomic() {
    auto s = Fixture();
    const auto initial = s.ReadOnly().ReadU32BE(kState+0x50);
    MustThrow<std::out_of_range>([&] { s.WriteVec3BE(kBody+0x8f8, {1,2,3}); });
    assert(s.ReadOnly().ReadU32BE(kState+0x50) == initial);
    MustThrow<std::out_of_range>([&] { s.WriteVec3BE(kState+0x51, {1,2,3}); });
    MustThrow<std::out_of_range>([&] { s.WriteU16BE(kState+0x1d, 0xffff); });
    MustThrow<std::out_of_range>([&] { s.WriteU16BE(0xFFFFFFFE, 0xffff); });
    MustThrow<std::out_of_range>([&] { RigidBodySetForce(s, 0, {1.f, 2.f, 3.f}); });
    MustThrow<std::out_of_range>([&] { RigidBodySetTorque(s, 0xFFFFFFFC, {1.f, 2.f, 3.f}); });
    MustThrow<std::invalid_argument>([] {
        (void)WiiMutableSnapshot({{kBody, {1,2,3,4}}, {kBody+2, {5,6,7,8}}});
    });
    // Crossing a mapped region boundary cannot partially overwrite.
    WiiMutableSnapshot separate({{0x80008000, {1,2,3,4}}, {0x80008004, {5,6,7,8}}});
    MustThrow<std::out_of_range>([&] {
        separate.WriteVec3BE(0x80008000, {1,2,3});
    });
    assert(separate.ReadOnly().ReadU32BE(0x80008000) == 0x01020304u);
    assert(separate.ReadOnly().ReadU32BE(0x80008004) == 0x05060708u);
}

void TestIntegrationPrefix() {
    auto active = Fixture(0, 0, 0);
    active.WriteVec3BE(kState + 0x20, {10.f, 20.f, 30.f});
    active.WriteVec3BE(kState + 0x3c, {0.5f, 0.f, 0.f});
    RigidBodySetForce(active, kBody, {2.f, 4.f, 6.f});
    assert(ApplyDoIntegrationVelocityPrefix(active, kBody, 0.25f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(active.ReadOnly(), kBody),
                 {10.25f, 20.5f, 30.75f}));
    assert(Equal(RigidBodyForce(active.ReadOnly(), kBody), {2.f, 4.f, 6.f}));
    // This prefix must not update location, orientation or angular state.
    assert(active.ReadOnly().ReadU32BE(kState + 0x10) == 0);
    assert(active.ReadOnly().ReadU32BE(kState + 0x30) == 0);

    auto sleeping = Fixture(0, 0, 1);
    sleeping.WriteVec3BE(kState + 0x20, {10.f, 20.f, 30.f});
    sleeping.WriteVec3BE(kState + 0x30, {1.f, -2.f, 3.f});
    RigidBodySetForce(sleeping, kBody, {4.f, 5.f, 6.f});
    assert(ApplyDoIntegrationVelocityPrefix(sleeping, kBody, 0.25f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyVelocity(sleeping.ReadOnly(), kBody), {0, 0, 0}));
    assert(sleeping.ReadOnly().ReadU32BE(kState + 0x30) == 0);
    assert(sleeping.ReadOnly().ReadU32BE(kState + 0x34) == 0);
    assert(sleeping.ReadOnly().ReadU32BE(kState + 0x38) == 0);
    assert(Equal(RigidBodyForce(sleeping.ReadOnly(), kBody), {4.f, 5.f, 6.f}));

    // Any nonzero byte takes the same branch, not only sleeping=1.
    auto modeling = Fixture(0, 0, 2);
    modeling.WriteVec3BE(kState + 0x20, {9.f, 8.f, 7.f});
    assert(ApplyDoIntegrationVelocityPrefix(modeling, kBody, 0.25f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyVelocity(modeling.ReadOnly(), kBody), {0, 0, 0}));

    // The original code branch clears two separated spans. A failure in
    // the second must not leave the first modified on the host snapshot.
    std::vector<std::uint8_t> body(0x300, 0);
    Put32(body, 0x70, kBody + 0x200);
    Put32(body, 0x200, kState);
    std::vector<std::uint8_t> velocity(12, 0);
    PutF32(velocity, 0, 5.f);
    WiiMutableSnapshot split({{kBody, std::move(body)},
                              {kState + 0x20, std::move(velocity)},
                              {kState + 0x5d, {1}}});
    MustThrow<std::out_of_range>([&] {
        (void)ApplyDoIntegrationVelocityPrefix(split, kBody, 0.25f);
    });
    assert(split.ReadOnly().ReadU32BE(kState + 0x20) == 0x40A00000u);
}


void TestTranslationAndTorquePrefix() {
    auto moving = Fixture(0, 0, 0);
    RigidBodySetPosition(moving, kBody, {100.f, 0.f, -2.f});
    RigidBodySetLinearVelocity(moving, kBody, {10.f, 20.f, 30.f});
    RigidBodySetAngularVelocity(moving, kBody, {1.f, 2.f, 3.f});
    RigidBodySetForce(moving, kBody, {2.f, 4.f, 6.f});
    RigidBodySetTorque(moving, kBody, {4.f, 8.f, -12.f});
    moving.WriteVec3BE(kState + 0x3C, {0.5f, 0.f, 0.f});

    assert(Equal(RigidBodyPosition(moving.ReadOnly(), kBody), {100.f, 0.f, -2.f}));
    assert(Equal(RigidBodyAngularVelocity(moving.ReadOnly(), kBody), {1.f, 2.f, 3.f}));
    assert(ApplyDoIntegrationTranslationPrefix(moving, kBody, 0.25f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(moving.ReadOnly(), kBody),
                 {10.25f, 20.5f, 30.75f}));
    assert(Equal(RigidBodyPosition(moving.ReadOnly(), kBody),
                 {102.5625f, 5.125f, 5.6875f}));
    assert(Equal(RigidBodyTorque(moving.ReadOnly(), kBody), {1.f, 2.f, -3.f}));
    assert(Equal(RigidBodyAngularVelocity(moving.ReadOnly(), kBody),
                 {1.f, 2.f, 3.f}));
    assert(Equal(RigidBodyForce(moving.ReadOnly(), kBody), {2.f, 4.f, 6.f}));

    // V7 has a deliberately narrower contract, for comparison.
    auto narrow = Fixture(0, 0, 0);
    RigidBodySetPosition(narrow, kBody, {100.f, 0.f, -2.f});
    RigidBodySetLinearVelocity(narrow, kBody, {10.f, 20.f, 30.f});
    RigidBodySetForce(narrow, kBody, {2.f, 4.f, 6.f});
    RigidBodySetTorque(narrow, kBody, {4.f, 8.f, -12.f});
    narrow.WriteVec3BE(kState + 0x3C, {0.5f, 0.f, 0.f});
    (void)ApplyDoIntegrationVelocityPrefix(narrow, kBody, 0.25f);
    assert(Equal(RigidBodyPosition(narrow.ReadOnly(), kBody), {100.f, 0.f, -2.f}));
    assert(Equal(RigidBodyTorque(narrow.ReadOnly(), kBody), {4.f, 8.f, -12.f}));

    auto inactive = Fixture(0, 0, 2);
    RigidBodySetPosition(inactive, kBody, {100.f, 2.f, 3.f});
    RigidBodySetLinearVelocity(inactive, kBody, {4.f, 5.f, 6.f});
    RigidBodySetAngularVelocity(inactive, kBody, {7.f, 8.f, 9.f});
    RigidBodySetTorque(inactive, kBody, {10.f, 11.f, 12.f});
    assert(ApplyDoIntegrationTranslationPrefix(inactive, kBody, 0.25f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyPosition(inactive.ReadOnly(), kBody), {100.f, 2.f, 3.f}));
    assert(Equal(RigidBodyTorque(inactive.ReadOnly(), kBody), {10.f, 11.f, 12.f}));
    assert(Equal(RigidBodyVelocity(inactive.ReadOnly(), kBody), {0, 0, 0}));
    assert(Equal(RigidBodyAngularVelocity(inactive.ReadOnly(), kBody), {0, 0, 0}));

    // The next two regions permit the velocity update but omit position.
    // A later access failure must not publish earlier writes.
    std::vector<std::uint8_t> body(0x300, 0);
    Put32(body, 0x70, kBody + 0x200);
    Put32(body, 0x200, kState);
    std::vector<std::uint8_t> velocity(12, 0);
    PutF32(velocity, 0, 5.f);
    std::vector<std::uint8_t> mass(4, 0);
    PutF32(mass, 0, 0.5f);
    std::vector<std::uint8_t> force(12, 0);
    PutF32(force, 0, 2.f);
    WiiMutableSnapshot missing_position({
        {kBody, std::move(body)},
        {kState + 0x20, std::move(velocity)},
        {kState + 0x3C, std::move(mass)},
        {kState + 0x50, std::move(force)},
        {kState + 0x5D, {0}},
        {kState + 0x60, std::vector<std::uint8_t>(12, 0)}
    });
    MustThrow<std::out_of_range>([&] {
        (void)ApplyDoIntegrationTranslationPrefix(missing_position, kBody, 0.25f);
    });
    assert(missing_position.ReadOnly().ReadU32BE(kState + 0x20) == 0x40A00000u);
}


void TestAngularInertiaPrefix() {
    auto moving = Fixture(0, 0, 0);
    RigidBodySetPosition(moving, kBody, {100.f, 0.f, -2.f});
    RigidBodySetLinearVelocity(moving, kBody, {10.f, 20.f, 30.f});
    RigidBodySetAngularVelocity(moving, kBody, {1.f, 2.f, 3.f});
    RigidBodySetForce(moving, kBody, {2.f, 4.f, 6.f});
    RigidBodySetTorque(moving, kBody, {4.f, 8.f, -12.f});
    moving.WriteVec3BE(kState + 0x3C, {0.5f, 0.f, 0.f});
    // The original 3x3 body transform has per-source rows at offsets
    // 0x84, 0x94 and 0xA4 (with a 4-byte gap between each triple).
    moving.WriteVec3BE(kBody + 0x84, {1.f, 0.f, 1.f});
    moving.WriteVec3BE(kBody + 0x94, {2.f, 1.f, 0.f});
    moving.WriteVec3BE(kBody + 0xA4, {0.f, 2.f, 1.f});
    assert(ApplyDoIntegrationAngularPrefix(moving, kBody, 0.25f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyPosition(moving.ReadOnly(), kBody),
                 {102.5625f, 5.125f, 5.6875f}));
    assert(Equal(RigidBodyVelocity(moving.ReadOnly(), kBody),
                 {10.25f, 20.5f, 30.75f}));
    assert(Equal(RigidBodyTorque(moving.ReadOnly(), kBody),
                 {5.f, -4.f, -2.f}));
    assert(Equal(RigidBodyAngularVelocity(moving.ReadOnly(), kBody),
                 {6.f, -2.f, 1.f}));
    assert(Equal(RigidBodyForce(moving.ReadOnly(), kBody), {2.f, 4.f, 6.f}));

    // Original state+0x5D != 0 returns early, skipping matrix reads.
    auto sleeping = Fixture(0, 0, 1);
    RigidBodySetPosition(sleeping, kBody, {4.f, 5.f, 6.f});
    RigidBodySetAngularVelocity(sleeping, kBody, {7.f, 8.f, 9.f});
    RigidBodySetTorque(sleeping, kBody, {10.f, 11.f, 12.f});
    assert(ApplyDoIntegrationAngularPrefix(sleeping, kBody, 1.f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyPosition(sleeping.ReadOnly(), kBody), {4.f, 5.f, 6.f}));
    assert(Equal(RigidBodyTorque(sleeping.ReadOnly(), kBody), {10.f, 11.f, 12.f}));
    assert(Equal(RigidBodyAngularVelocity(sleeping.ReadOnly(), kBody), {0, 0, 0}));

    // All V8 writes can succeed on private regions, yet a missing BODY
    // transform must cause V9 to reject WITHOUT exposing partial results.
    std::vector<std::uint8_t> body(0x80, 0);
    Put32(body, 0x70, kBody + 0x200);
    std::vector<std::uint8_t> wrapper(4, 0);
    Put32(wrapper, 0, kState);
    std::vector<std::uint8_t> mass(4, 0);
    PutF32(mass, 0, 0.5f);
    std::vector<std::uint8_t> old_vel(12, 0);
    PutF32(old_vel, 0, 10.f);
    std::vector<std::uint8_t> torque(12, 0);
    PutF32(torque, 0, 4.f);
    WiiMutableSnapshot missing_matrix({
        {kBody, std::move(body)},
        {kBody + 0x200, std::move(wrapper)},
        {kState + 0x10, std::vector<std::uint8_t>(12, 0)},
        {kState + 0x20, std::move(old_vel)},
        {kState + 0x30, std::vector<std::uint8_t>(12, 0)},
        {kState + 0x3C, std::move(mass)},
        {kState + 0x50, std::vector<std::uint8_t>(12, 0)},
        {kState + 0x5D, {0}},
        {kState + 0x60, std::move(torque)}
    });
    MustThrow<std::out_of_range>([&] {
        (void)ApplyDoIntegrationAngularPrefix(missing_matrix, kBody, 0.5f);
    });
    assert(missing_matrix.ReadOnly().ReadU32BE(kState + 0x20) == 0x41200000u);
    assert(missing_matrix.ReadOnly().ReadU32BE(kState + 0x60) == 0x40800000u);
}


void TestVelocitySaturationPrefix() {
    auto moving = Fixture(0, 0, 0);
    RigidBodySetLinearVelocity(moving, kBody, {350.f, -350.f, 300.f});
    RigidBodySetAngularVelocity(moving, kBody, {35.f, -35.f, 30.f});
    assert(ApplyDoIntegrationClampedAngularPrefix(moving, kBody, 1.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(moving.ReadOnly(), kBody),
                 {300.f, -300.f, 300.f}));
    assert(Equal(RigidBodyAngularVelocity(moving.ReadOnly(), kBody),
                 {30.f, -30.f, 30.f}));
    // The original position update runs BEFORE velocity saturation.
    // Do not mistake the post-clamp speed for the integrated displacement.
    assert(Equal(RigidBodyPosition(moving.ReadOnly(), kBody),
                 {350.f, -350.f, 300.f}));
    auto limits = Fixture(0, 0, 0);
    RigidBodySetLinearVelocity(limits, kBody, {-300.f, 300.f, 0.f});
    RigidBodySetAngularVelocity(limits, kBody, {-30.f, 30.f, 0.f});
    assert(ApplyDoIntegrationClampedAngularPrefix(limits, kBody, 0.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(limits.ReadOnly(), kBody),
                 {-300.f, 300.f, 0.f}));
    assert(Equal(RigidBodyAngularVelocity(limits.ReadOnly(), kBody),
                 {-30.f, 30.f, 0.f}));

    // PowerPC ordered fcmpo branches select the positive limit for NaN.
    auto special = Fixture(0, 0, 0);
    const float nan = std::numeric_limits<float>::quiet_NaN();
    const float inf = std::numeric_limits<float>::infinity();
    RigidBodySetLinearVelocity(special, kBody, {nan, inf, -inf});
    RigidBodySetAngularVelocity(special, kBody, {nan, inf, -inf});
    assert(ApplyDoIntegrationClampedAngularPrefix(special, kBody, 1.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(special.ReadOnly(), kBody),
                 {300.f, 300.f, -300.f}));
    assert(Equal(RigidBodyAngularVelocity(special.ReadOnly(), kBody),
                 {30.f, 30.f, -30.f}));

    auto inactive = Fixture(0, 0, 1);
    RigidBodySetPosition(inactive, kBody, {2.f, 4.f, 6.f});
    RigidBodySetLinearVelocity(inactive, kBody, {350.f, -350.f, 300.f});
    RigidBodySetAngularVelocity(inactive, kBody, {35.f, -35.f, 30.f});
    assert(ApplyDoIntegrationClampedAngularPrefix(inactive, kBody, 1.f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyPosition(inactive.ReadOnly(), kBody), {2.f, 4.f, 6.f}));
    assert(Equal(RigidBodyVelocity(inactive.ReadOnly(), kBody), {0, 0, 0}));
    assert(Equal(RigidBodyAngularVelocity(inactive.ReadOnly(), kBody), {0, 0, 0}));
}


void TestV10IndependentPhaseBoundaries() {
    // Synthetic control: zero timestep preserves position and velocity but
    // consumes the torque workspace in the verified V8/V9 sequence.
    auto zero = Fixture(0, 0, 0);
    RigidBodySetPosition(zero, kBody, {17.f, -5.f, 9.f});
    RigidBodySetLinearVelocity(zero, kBody, {3.f, -4.f, 5.f});
    RigidBodySetAngularVelocity(zero, kBody, {6.f, 7.f, -8.f});
    RigidBodySetForce(zero, kBody, {12.f, 14.f, 16.f});
    RigidBodySetTorque(zero, kBody, {2.f, -3.f, 4.f});
    zero.WriteVec3BE(kState + 0x3C, {0.25f, 0.f, 0.f});
    zero.WriteVec3BE(kBody + 0x84, {2.f, 0.f, 0.f});
    zero.WriteVec3BE(kBody + 0x94, {0.f, 3.f, 0.f});
    zero.WriteVec3BE(kBody + 0xA4, {0.f, 0.f, 4.f});
    assert(ApplyDoIntegrationClampedAngularPrefix(zero, kBody, 0.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyPosition(zero.ReadOnly(), kBody), {17.f, -5.f, 9.f}));
    assert(Equal(RigidBodyVelocity(zero.ReadOnly(), kBody), {3.f, -4.f, 5.f}));
    assert(Equal(RigidBodyAngularVelocity(zero.ReadOnly(), kBody), {6.f, 7.f, -8.f}));
    assert(Equal(RigidBodyTorque(zero.ReadOnly(), kBody), {0.f, 0.f, 0.f}));
    assert(Equal(RigidBodyForce(zero.ReadOnly(), kBody), {12.f, 14.f, 16.f}));

    // Any nonzero status, including 255, bypasses all active-path reads.
    std::vector<std::uint8_t> owner(0x300, 0);
    Put32(owner, 0x70, kBody + 0x200);
    Put32(owner, 0x200, kState);
    std::vector<std::uint8_t> linear(12, 0), angular(12, 0);
    PutF32(linear, 0, 9.f);
    PutF32(angular, 0, -7.f);
    WiiMutableSnapshot inactive({
        {kBody, std::move(owner)},
        {kState + 0x20, std::move(linear)},
        {kState + 0x30, std::move(angular)},
        {kState + 0x5D, {255}}
    });
    assert(ApplyDoIntegrationClampedAngularPrefix(inactive, kBody, 0.125f) ==
           IntegrationPrefixPath::inactive_cleared);
    assert(Equal(RigidBodyVelocity(inactive.ReadOnly(), kBody), {0.f, 0.f, 0.f}));
    assert(Equal(RigidBodyAngularVelocity(inactive.ReadOnly(), kBody), {0.f, 0.f, 0.f}));

    // Asymmetric nonidentity matrix detects accidental transpose or identity.
    auto cross = Fixture(0, 0, 0);
    RigidBodySetTorque(cross, kBody, {1.f, 2.f, 3.f});
    cross.WriteVec3BE(kBody + 0x84, {0.f, 1.f, 2.f});
    cross.WriteVec3BE(kBody + 0x94, {3.f, 0.f, 4.f});
    cross.WriteVec3BE(kBody + 0xA4, {5.f, 6.f, 0.f});
    assert(ApplyDoIntegrationAngularPrefix(cross, kBody, 1.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyTorque(cross.ReadOnly(), kBody), {21.f, 19.f, 10.f}));
    assert(Equal(RigidBodyAngularVelocity(cross.ReadOnly(), kBody), {21.f, 19.f, 10.f}));
}


void TestV10OrderedClampNeighbors() {
    // Values immediately on either side of each documented Wii clamp.
    // This catches accidental >= / <= reversal and incorrect limits.
    const float above_linear = std::nextafter(300.f, std::numeric_limits<float>::infinity());
    const float below_linear = std::nextafter(-300.f, -std::numeric_limits<float>::infinity());
    const float inside_linear = std::nextafter(300.f, 0.f);
    const float above_angular = std::nextafter(30.f, std::numeric_limits<float>::infinity());
    const float below_angular = std::nextafter(-30.f, -std::numeric_limits<float>::infinity());
    const float inside_angular = std::nextafter(-30.f, 0.f);
    auto s = Fixture(0, 0, 0);
    RigidBodySetLinearVelocity(s, kBody, {above_linear, below_linear, inside_linear});
    RigidBodySetAngularVelocity(s, kBody, {above_angular, below_angular, inside_angular});
    assert(ApplyDoIntegrationClampedAngularPrefix(s, kBody, 1.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    assert(Equal(RigidBodyVelocity(s.ReadOnly(), kBody),
                 {300.f, -300.f, inside_linear}));
    assert(Equal(RigidBodyAngularVelocity(s.ReadOnly(), kBody),
                 {30.f, -30.f, inside_angular}));
    // Translation precedes the clamp, even one ULP beyond the limit.
    assert(Equal(RigidBodyPosition(s.ReadOnly(), kBody),
                 {above_linear, below_linear, inside_linear}));
}


void TestV10MatrixAndClampComposition() {
    // Independent arithmetic oracle for a nontrivial, asymmetric body matrix.
    // V9 transforms timestep-scaled torque; V10 clamps the resulting angular
    // velocity, but preserves the unclamped torque workspace.
    auto s = Fixture(0, 0, 0);
    RigidBodySetAngularVelocity(s, kBody, {29.f, -29.f, 5.f});
    RigidBodySetTorque(s, kBody, {4.f, -6.f, 8.f});
    s.WriteVec3BE(kBody + 0x84, {2.f, 1.f, 0.f});
    s.WriteVec3BE(kBody + 0x94, {0.f, 3.f, -1.f});
    s.WriteVec3BE(kBody + 0xA4, {1.f, 0.f, 4.f});
    assert(ApplyDoIntegrationClampedAngularPrefix(s, kBody, 2.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    // Scaled torque (8,-12,16) maps to (32,-28,76).
    assert(Equal(RigidBodyTorque(s.ReadOnly(), kBody), {32.f, -28.f, 76.f}));
    assert(Equal(RigidBodyAngularVelocity(s.ReadOnly(), kBody), {30.f, -30.f, 30.f}));
    assert(Equal(RigidBodyVelocity(s.ReadOnly(), kBody), {0.f, 0.f, 0.f}));
}

} // namespace

int main() {
    TestFlags();
    TestForces();
    TestRejectedWritesAreAtomic();
    TestIntegrationPrefix();
    TestTranslationAndTorquePrefix();
    TestAngularInertiaPrefix();
    TestVelocitySaturationPrefix();
    TestV10IndependentPhaseBoundaries();
    TestV10OrderedClampNeighbors();
    TestV10MatrixAndClampComposition();
}
