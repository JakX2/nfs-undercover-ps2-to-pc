#include "wii_rigidbody_collision_args.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBase = 0x80060000u;
constexpr std::uint32_t kState = kBase + 0x400u;
constexpr std::uint32_t kPrimitive = kBase + 0x900u;

void Put32(std::vector<std::uint8_t>& b, std::size_t pos, std::uint32_t v) {
    assert(pos + 4 <= b.size());
    b[pos] = std::uint8_t(v >> 24);
    b[pos+1] = std::uint8_t(v >> 16);
    b[pos+2] = std::uint8_t(v >> 8);
    b[pos+3] = std::uint8_t(v);
}
void Check(Vec3 a, Vec3 b) {
    assert(std::fabs(a.x-b.x) < 0.0001f);
    assert(std::fabs(a.y-b.y) < 0.0001f);
    assert(std::fabs(a.z-b.z) < 0.0001f);
}
template<typename Fn> void ExpectOutOfRange(Fn&& fn) {
    bool threw = false;
    try { fn(); } catch (const std::out_of_range&) { threw = true; }
    assert(threw);
}

WiiMutableSnapshot MakeFixture(std::uint32_t shape) {
    std::vector<std::uint8_t> b(0x1000u, 0);
    Put32(b, 0x900 + 0x24, shape);
    WiiMutableSnapshot m({{kBase, std::move(b)}});
    m.WriteVec3BE(kPrimitive + 0x18, {3.f, 4.f, 5.f});
    m.WriteVec3BE(kPrimitive + 0x28, {2.f, -1.f, 0.5f});
    m.WriteVec3BE(kPrimitive + 0x38, {11.5f, -17.f, 34.5f});
    m.WriteVec3BE(kState + 0x10, {10.f, -20.f, 30.f});
    m.WriteMatrix4BE(kState + 0x70, {
        1.f, 2.f, 3.f, 0.f,
        4.f, 5.f, 6.f, 0.f,
        7.f, 8.f, 9.f, 0.f,
        0.f, 0.f, 0.f, 1.f
    });
    return m;
}

void TestShape2UsesLiteralIdentityAndRetainsPreparePosition() {
    auto m = MakeFixture(2);
    // Shape 2 must not require readable local or state quaternion fields.
    const auto a = BuildWiiPrimitiveCollisionCall(m.ReadOnly(), kPrimitive, kState);
    assert(a.shape == 2 && a.uses_identity_orientation);
    Check(a.primitive_parameters, {3.f, 4.f, 5.f});
    Check(a.world_position, {11.5f, -17.f, 34.5f});
    Check(a.world_delta, {0.f, 0.f, 0.f});
    const WiiMatrix4 identity{1.f,0.f,0.f,0.f, 0.f,1.f,0.f,0.f,
                              0.f,0.f,1.f,0.f, 0.f,0.f,0.f,1.f};
    assert(a.orientation == identity);
    Check(WiiPrimitivePreparedWorldPosition(m.ReadOnly(), kPrimitive),
          {11.5f,-17.f,34.5f});
}

void TestChangedStateGivesWorldDelta() {
    auto m = MakeFixture(2);
    m.WriteVec3BE(kState + 0x10, {13.f,-18.f,34.f});
    const auto a = BuildWiiPrimitiveCollisionCall(m.ReadOnly(), kPrimitive, kState);
    Check(a.world_position, {14.5f,-15.f,38.5f});
    Check(a.world_delta, {3.f,2.f,4.f});
}

void TestQuaternionProductOrderForOtherShapes() {
    auto m = MakeFixture(3);
    constexpr float h = 0.7071067811865475244f;
    // State: 90 degrees around Z, local primitive: 90 around X.
    // A noncommuting pair distinguishes state*primitive from primitive*state.
    m.WriteVec4BE(kState, {0.f,0.f,h,h});
    m.WriteVec4BE(kPrimitive + 0x08, {h,0.f,0.f,h});
    const auto a = BuildWiiPrimitiveCollisionCall(m.ReadOnly(), kPrimitive,kState);
    assert(a.shape == 3 && !a.uses_identity_orientation);
    assert(std::fabs(a.orientation[1] - 1.f) < 0.0001f);
    assert(std::fabs(a.orientation[6] - 1.f) < 0.0001f);
    assert(std::fabs(a.orientation[8] - 1.f) < 0.0001f);
    assert(std::fabs(a.orientation[2]) < 0.0001f);
    Check(a.world_delta, {0.f,0.f,0.f});
}

void TestMalformedInputsFailClosed() {
    auto m = MakeFixture(2);
    ExpectOutOfRange([&] {
        (void)BuildWiiPrimitiveCollisionCall(m.ReadOnly(), 0, kState);
    });
    ExpectOutOfRange([&] {
        (void)BuildWiiPrimitiveCollisionCall(m.ReadOnly(), kPrimitive, 0xfffffff0u);
    });
    ExpectOutOfRange([&] {
        (void)BuildWiiPrimitiveCollisionCall(m.ReadOnly(), 0x90000000u,kState);
    });
}
}

int main() {
    TestShape2UsesLiteralIdentityAndRetainsPreparePosition();
    TestChangedStateGivesWorldDelta();
    TestQuaternionProductOrderForOtherShapes();
    TestMalformedInputsFailClosed();
}
