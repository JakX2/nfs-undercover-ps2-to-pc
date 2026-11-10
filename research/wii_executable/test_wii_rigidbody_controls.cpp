#include "wii_rigidbody_controls.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
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
    MustThrow<std::out_of_range>([&] { RigidBodySetForce(s, 0); });
    MustThrow<std::out_of_range>([&] { RigidBodySetTorque(s, 0xFFFFFFFC); });
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
} // namespace

int main() {
    TestFlags();
    TestForces();
    TestRejectedWritesAreAtomic();
}
