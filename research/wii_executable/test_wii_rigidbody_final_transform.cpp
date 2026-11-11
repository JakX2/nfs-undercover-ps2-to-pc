#include "wii_rigidbody_final_transform.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;

void Put32(std::vector<std::uint8_t>& memory, std::size_t offset,
           std::uint32_t value) {
    assert(offset + 4 <= memory.size());
    memory[offset] = std::uint8_t(value >> 24);
    memory[offset + 1] = std::uint8_t(value >> 16);
    memory[offset + 2] = std::uint8_t(value >> 8);
    memory[offset + 3] = std::uint8_t(value);
}
bool Near(float x, float y, float tolerance=0.0001f) {
    return std::abs(x - y) <= tolerance;
}
void CheckMatrix(const WiiMatrix4& found, const WiiMatrix4& expected,
                 float tolerance=0.0001f) {
    for (std::size_t i = 0; i < 16; ++i)
        assert(Near(found[i], expected[i], tolerance));
}

template<typename Error, typename Callable>
void MustThrow(Callable f) {
    bool threw = false;
    try { f(); } catch (const Error&) { threw = true; }
    assert(threw);
}

WiiMutableSnapshot Fixture(std::uint8_t status=0) {
    std::vector<std::uint8_t> bytes(0x900, 0);
    Put32(bytes, 0x70, kBody + 0x200);
    Put32(bytes, 0x200, kState);
    WiiMutableSnapshot snapshot({{kBody, std::move(bytes)}});
    snapshot.WriteVec4BE(kState, {0.f, 0.f, 0.f, 1.f});
    snapshot.WriteVec3BE(kState + 0x40, {2.f, 4.f, 8.f});
    snapshot.WriteVec3BE(kBody + 0xE4, {1.f, 2.f, 3.f});
    const WiiMatrix4 identity {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    };
    snapshot.WriteMatrix4BE(kState + 0x70, identity);
    snapshot.WriteMatrix4BE(kBody + 0x84, identity);
    if (status) {
        // Status is an individual byte in the original state structure.
        // The constructor's original-free region can set this safely.
        std::vector<std::uint8_t> buffer(0x900, 0);
        Put32(buffer, 0x70, kBody + 0x200);
        Put32(buffer, 0x200, kState);
        buffer[0x400 + 0x5D] = status;
        WiiMutableSnapshot inactive({{kBody, std::move(buffer)}});
        inactive.WriteVec4BE(kState, {0,0,0,1});
        inactive.WriteMatrix4BE(kState + 0x70, identity);
        inactive.WriteMatrix4BE(kBody + 0x84, identity);
        return inactive;
    }
    return snapshot;
}

void TestZeroRotationStillRebuildsBodyMatrix() {
    auto s = Fixture();
    RigidBodySetPosition(s, kBody, {10.f, 20.f, 30.f});
    assert(ApplyDoIntegrationPostOrientationStage(s, kBody, 0.25f) ==
           IntegrationPrefixPath::active_velocity_updated);
    const WiiMatrix4 expected{
        .5f,0,0,0,
        0,.25f,0,0,
        0,0,.125f,0,
        0,0,0,1
    };
    CheckMatrix(RigidBodyBodyMatrix(s.ReadOnly(), kBody), expected);
    auto pos = RigidBodyPosition(s.ReadOnly(), kBody);
    assert(Near(pos.x, 10.f) && Near(pos.y, 20.f) && Near(pos.z, 30.f));
    assert(Near(RigidBodyQuaternion(s.ReadOnly(), kBody).w, 1.f));
}

void TestRotationChangesTensorAndCenterCorrection() {
    auto s = Fixture();
    RigidBodySetAngularVelocity(s, kBody, {0.f,0.f,2.f});
    RigidBodySetPosition(s, kBody, {10.f,20.f,30.f});
    assert(ApplyDoIntegrationPostOrientationStage(s, kBody, 0.5f) ==
           IntegrationPrefixPath::active_velocity_updated);
    const auto rot = RigidBodyOrientationMatrix(s.ReadOnly(), kBody);
    assert(Near(rot[0], .6f) && Near(rot[1], .8f));
    assert(Near(rot[4], -.8f) && Near(rot[5], .6f));
    const WiiMatrix4 expected{
        .34f,.12f,0,0,
        .12f,.41f,0,0,
        0,0,.125f,0,
        0,0,0,1
    };
    CheckMatrix(RigidBodyBodyMatrix(s.ReadOnly(), kBody), expected);
    const auto pos = RigidBodyPosition(s.ReadOnly(), kBody);
    assert(Near(pos.x, 12.f) && Near(pos.y, 20.f) && Near(pos.z, 30.f));
    const auto q = RigidBodyQuaternion(s.ReadOnly(), kBody);
    assert(Near(q.z, 0.4472136f) && Near(q.w, .8944272f));
}

void TestThresholdAndNegativeValues() {
    auto s = Fixture();
    s.WriteVec3BE(kState + 0x40, {0.0000005f,0.000002f,-4.f});
    (void)ApplyDoIntegrationPostOrientationStage(s, kBody, 0.f);
    const auto m = RigidBodyBodyMatrix(s.ReadOnly(), kBody);
    assert(Near(m[0], .0000005f, 0.0000000001f));
    assert(Near(m[5], 500000.f, 0.1f));
    assert(m[10] == -4.f);
    assert(m[15] == 1.f);
}

void TestInactiveSkipsBodyTransform() {
    auto s = Fixture(2);
    RigidBodySetPosition(s, kBody, {4.f,5.f,6.f});
    RigidBodySetLinearVelocity(s, kBody, {11.f,12.f,13.f});
    RigidBodySetAngularVelocity(s, kBody, {14.f,15.f,16.f});
    const auto original = RigidBodyBodyMatrix(s.ReadOnly(), kBody);
    assert(ApplyDoIntegrationPostOrientationStage(s, kBody, .5f) ==
           IntegrationPrefixPath::inactive_cleared);
    CheckMatrix(RigidBodyBodyMatrix(s.ReadOnly(), kBody), original);
    const auto p = RigidBodyPosition(s.ReadOnly(), kBody);
    assert(p.x == 4.f && p.y == 5.f && p.z == 6.f);
    const auto v = RigidBodyVelocity(s.ReadOnly(), kBody);
    assert(v.x == 0 && v.y == 0 && v.z == 0);
}

void TestMissingBodyMatrixWriteRollsBackWholeTick() {
    // The initial 3x3 body matrix needed by V9 fits before +0xB0,
    // but V12's 4x4 update of body+0x84..+0xC0 does not. Center and
    // wrapper are separately mapped so all earlier phases can execute.
    std::vector<std::uint8_t> body(0xB0, 0);
    Put32(body, 0x70, kBody + 0x200);
    std::vector<std::uint8_t> wrapper(4, 0);
    Put32(wrapper, 0, kState);
    std::vector<std::uint8_t> state(0xB0, 0);
    WiiMutableSnapshot s({{kBody, std::move(body)},
                          {kBody + 0xE4, std::vector<std::uint8_t>(12, 0)},
                          {kBody + 0x200, std::move(wrapper)},
                          {kState, std::move(state)}});
    s.WriteVec4BE(kState, {0,0,0,1});
    s.WriteVec3BE(kState+0x40, {2,4,8});
    s.WriteVec3BE(kState+0x20, {10,0,0});
    s.WriteVec3BE(kBody+0x84, {1,0,0});
    s.WriteVec3BE(kBody+0x94, {0,1,0});
    s.WriteVec3BE(kBody+0xA4, {0,0,1});
    const WiiMatrix4 identity{
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1
    };
    s.WriteMatrix4BE(kState+0x70, identity);
    MustThrow<std::out_of_range>([&] {
        (void)ApplyDoIntegrationPostOrientationStage(s, kBody, .5f);
    });
    assert(s.ReadOnly().ReadU32BE(kState+0x20) == 0x41200000u);
    assert(s.ReadOnly().ReadU32BE(kState+0x10) == 0);
    assert(s.ReadOnly().ReadU32BE(kBody+0x84) == 0x3F800000u);
}

void TestReciprocalStrictBoundaryAndUnaffectedState() {
    // Synthetic V12 regression: the Wii ordered GT comparison is strict.
    // Exact threshold and zero remain unchanged; a larger positive input
    // is reciprocated. This is not a runtime differential test.
    auto s = Fixture();
    const float threshold = 0.000001f;
    s.WriteVec3BE(kState + 0x40, {threshold, 0.f, 0.000002f});
    RigidBodySetPosition(s, kBody, {-3.f, 7.f, 11.f});
    const auto prior = RigidBodyPosition(s.ReadOnly(), kBody);
    assert(ApplyDoIntegrationPostOrientationStage(s, kBody, 0.f) ==
           IntegrationPrefixPath::active_velocity_updated);
    const auto matrix = RigidBodyBodyMatrix(s.ReadOnly(), kBody);
    assert(Near(matrix[0], threshold, 0.0000000001f));
    assert(matrix[5] == 0.f);
    assert(Near(matrix[10], 500000.f, 0.1f));
    assert(matrix[15] == 1.f);
    const auto after = RigidBodyPosition(s.ReadOnly(), kBody);
    assert(Near(after.x, prior.x));
    assert(Near(after.y, prior.y));
    assert(Near(after.z, prior.z));
}

} // namespace

int main() {
    TestZeroRotationStillRebuildsBodyMatrix();
    TestRotationChangesTensorAndCenterCorrection();
    TestThresholdAndNegativeValues();
    TestInactiveSkipsBodyTransform();
    TestMissingBodyMatrixWriteRollsBackWholeTick();
    TestReciprocalStrictBoundaryAndUnaffectedState();
}
