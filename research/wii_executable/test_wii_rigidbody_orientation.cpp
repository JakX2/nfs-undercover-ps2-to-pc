#include "wii_rigidbody_orientation.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;
using undercover::attrib::WiiAddressSpace;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;

void Put32(std::vector<std::uint8_t>& v, std::size_t at, std::uint32_t x) {
    assert(at + 4 <= v.size());
    v[at] = static_cast<std::uint8_t>(x >> 24);
    v[at + 1] = static_cast<std::uint8_t>(x >> 16);
    v[at + 2] = static_cast<std::uint8_t>(x >> 8);
    v[at + 3] = static_cast<std::uint8_t>(x);
}
void PutFloat(std::vector<std::uint8_t>& v, std::size_t at, float f) {
    std::uint32_t bits = 0;
    static_assert(sizeof(bits) == sizeof(f), "float32 required");
    std::memcpy(&bits, &f, sizeof(bits));
    Put32(v, at, bits);
}
bool Near(float x, float y, float tol=0.00002f) {
    return std::abs(x-y) <= tol;
}
template <typename Error, typename Fn> void ExpectThrows(Fn fn) {
    bool threw = false;
    try { fn(); } catch (const Error&) { threw = true; }
    assert(threw);
}

WiiMutableSnapshot Fixture(std::uint8_t status=0, bool complete_matrix=true) {
    const std::size_t length = complete_matrix ? 0x900 : 0x300;
    std::vector<std::uint8_t> body(length, 0);
    Put32(body, 0x70, kBody + 0x200);
    if (complete_matrix) {
        Put32(body, 0x200, kState);
        PutFloat(body, 0x400+12, 1.f); // orientation quaternion w
        PutFloat(body, 0x400+0x3C, 1.f); // inverse mass
        body[0x400+0x5D] = status;
        return WiiMutableSnapshot({{kBody, std::move(body)}});
    }
    // The wrapper lives inside the body fixture region for both paths.
    Put32(body, 0x200, kState);
    // Map everything necessary to run V10, but deliberately leave
    // orientation matrix state+0x70 through +0xAC unavailable.
    std::vector<std::uint8_t> state(0x70, 0);
    PutFloat(state, 12, 1.f);
    PutFloat(state, 0x3C, 1.f);
    state[0x5D] = status;
    return WiiMutableSnapshot({{kBody, std::move(body)},
                               {kState, std::move(state)}});
}

void TestWiiQuaternionMatrixFormula() {
    const auto id = WiiQuaternionToMatrix4({0.f, 0.f, 0.f, 1.f});
    for (std::size_t i = 0; i < id.size(); ++i)
        assert(id[i] == ((i % 5) == 0 ? 1.f : 0.f));
    const float z = std::sqrt(0.5f);
    const auto rot = WiiQuaternionToMatrix4({0.f, 0.f, z, z});
    assert(Near(rot[0], 0.f));
    assert(Near(rot[1], 1.f));
    assert(Near(rot[4], -1.f));
    assert(Near(rot[5], 0.f));
    assert(Near(rot[10], 1.f) && Near(rot[15], 1.f));
    assert(rot[3] == 0.f && rot[7] == 0.f && rot[11] == 0.f);
}

void TestQuaternionAndMatrixIntegration() {
    auto s = Fixture();
    RigidBodySetAngularVelocity(s, kBody, {0.f, 0.f, 2.f});
    assert(ApplyDoIntegrationOrientationPrefix(s, kBody, 0.5f) ==
           IntegrationPrefixPath::active_velocity_updated);
    const auto q = RigidBodyQuaternion(s.ReadOnly(), kBody);
    assert(Near(q.x, 0.f) && Near(q.y, 0.f));
    assert(Near(q.z, 0.4472135955f));
    assert(Near(q.w, 0.894427191f));
    const auto matrix = RigidBodyOrientationMatrix(s.ReadOnly(), kBody);
    assert(Near(matrix[0], 0.6f) && Near(matrix[1], 0.8f));
    assert(Near(matrix[4], -0.8f) && Near(matrix[5], 0.6f));
    assert(Near(matrix[10], 1.f) && Near(matrix[15], 1.f));
    for (std::size_t index : {3u, 7u, 11u, 12u, 13u, 14u})
        assert(matrix[index] == 0.f);
    assert(Near(RigidBodyAngularVelocity(s.ReadOnly(), kBody).z, 2.f));
    assert(Near(RigidBodyPosition(s.ReadOnly(), kBody).z, 0.f));
    assert(s.ReadOnly().ReadU32BE(kState + 0x0C) ==
           0x3F64F92Eu || Near(q.w, 0.894427191f));
}

void TestZeroAngularSkipsOrientation() {
    auto s = Fixture();
    // Deliberately invalid quaternion: original skips normalization when
    // the entire clamped angular velocity vector is exactly zero.
    s.WriteVec4BE(kState, {0.f, 0.f, 0.f, 0.f});
    std::array<float, 16> marker{};
    marker[0] = 17.f;
    s.WriteMatrix4BE(kState + 0x70, marker);
    (void)ApplyDoIntegrationOrientationPrefix(s, kBody, 1.f);
    assert(RigidBodyQuaternion(s.ReadOnly(), kBody).w == 0.f);
    assert(RigidBodyOrientationMatrix(s.ReadOnly(), kBody)[0] == 17.f);

    // Inactive state returns before checking the quaternion too.
    auto inactive = Fixture(2);
    RigidBodySetAngularVelocity(inactive, kBody, {4.f, 5.f, 6.f});
    (void)ApplyDoIntegrationOrientationPrefix(inactive, kBody, 0.5f);
    assert(RigidBodyQuaternion(inactive.ReadOnly(), kBody).w == 1.f);
    assert(RigidBodyAngularVelocity(inactive.ReadOnly(), kBody).x == 0.f);
    assert(RigidBodyOrientationMatrix(inactive.ReadOnly(), kBody)[0] == 0.f);
}

void TestExceptionsLeaveSnapshotUnchanged() {
    auto bad = Fixture();
    bad.WriteVec4BE(kState, {0.f, 0.f, 0.f, 0.f});
    RigidBodySetAngularVelocity(bad, kBody, {0.f, 0.f, 2.f});
    RigidBodySetLinearVelocity(bad, kBody, {12.f, 0.f, 0.f});
    ExpectThrows<std::domain_error>([&] {
        (void)ApplyDoIntegrationOrientationPrefix(bad, kBody, 1.f);
    });
    assert(RigidBodyQuaternion(bad.ReadOnly(), kBody).w == 0.f);
    assert(RigidBodyPosition(bad.ReadOnly(), kBody).x == 0.f);
    assert(RigidBodyVelocity(bad.ReadOnly(), kBody).x == 12.f);

    auto split = Fixture(0, false);
    RigidBodySetAngularVelocity(split, kBody, {0.f, 0.f, 2.f});
    RigidBodySetLinearVelocity(split, kBody, {12.f, 0.f, 0.f});
    const auto before = RigidBodyQuaternion(split.ReadOnly(), kBody);
    ExpectThrows<std::out_of_range>([&] {
        (void)ApplyDoIntegrationOrientationPrefix(split, kBody, 0.5f);
    });
    assert(RigidBodyQuaternion(split.ReadOnly(), kBody).w == before.w);
    assert(RigidBodyVelocity(split.ReadOnly(), kBody).x == 12.f);
    assert(RigidBodyPosition(split.ReadOnly(), kBody).x == 0.f);

    WiiMutableSnapshot short_span({{0x80001000, std::vector<std::uint8_t>(60, 0)}});
    std::array<float, 16> identity{};
    identity[0] = identity[5] = identity[10] = identity[15] = 1.f;
    ExpectThrows<std::out_of_range>([&] {
        short_span.WriteMatrix4BE(0x80001000, identity);
    });
    assert(short_span.ReadOnly().ReadU32BE(0x80001000) == 0u);
    ExpectThrows<std::out_of_range>([&] {
        short_span.WriteVec4BE(0x80001032, {1.f, 2.f, 3.f, 4.f});
    });
    assert(short_span.ReadOnly().ReadU32BE(0x80001000) == 0u);
}
} // namespace

int main() {
    TestWiiQuaternionMatrixFormula();
    TestQuaternionAndMatrixIntegration();
    TestZeroAngularSkipsOrientation();
    TestExceptionsLeaveSnapshotUnchanged();
}
