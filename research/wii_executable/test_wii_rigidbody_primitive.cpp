#include "wii_rigidbody_primitive.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;
constexpr std::uint32_t kFirst = kBody + 0x900u;
constexpr std::uint32_t kSecond = kBody + 0xA00u;
constexpr std::uint32_t kSentinel = kBody + 0x104u;

void Put32(std::vector<std::uint8_t>& bytes,
           std::size_t offset, std::uint32_t v) {
    assert(offset + 4 <= bytes.size());
    bytes[offset] = std::uint8_t(v >> 24);
    bytes[offset + 1] = std::uint8_t(v >> 16);
    bytes[offset + 2] = std::uint8_t(v >> 8);
    bytes[offset + 3] = std::uint8_t(v);
}

bool Near(float a, float b, float tolerance=0.00005f) {
    return std::isfinite(a) && std::isfinite(b) &&
           std::fabs(a - b) < tolerance;
}

void ExpectVector(Vec3 got, Vec3 expected) {
    assert(Near(got.x, expected.x));
    assert(Near(got.y, expected.y));
    assert(Near(got.z, expected.z));
}

template <class Error, class Fn> void MustThrow(Fn f) {
    bool caught = false;
    try { f(); } catch (const Error&) { caught = true; }
    assert(caught);
}

WiiMutableSnapshot Fixture(bool two_nodes=true, std::uint8_t status=0) {
    std::vector<std::uint8_t> bytes(0x1200, 0);
    Put32(bytes, 0x70, kBody + 0x200);
    Put32(bytes, 0x200, kState);
    Put32(bytes, 0x104, kFirst);
    Put32(bytes, 0x900, two_nodes ? kSecond : kSentinel);
    Put32(bytes, 0xA00, kSentinel);
    bytes[0x400 + 0x5D] = status;
    WiiMutableSnapshot memory({{kBody, std::move(bytes)}});
    memory.WriteVec4BE(kState, {0.f,0.f,0.f,1.f});
    memory.WriteVec3BE(kState + 0x40, {1.f,1.f,1.f});
    memory.WriteMatrix4BE(kBody + 0x84, {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    });
    // Nontrivial matrix catches row/column transpositions.
    memory.WriteMatrix4BE(kState + 0x70, {
        1.f, 2.f, 3.f, 0.f,
        4.f, 5.f, 6.f, 0.f,
        7.f, 8.f, 9.f, 0.f,
        0.f, 0.f, 0.f, 1.f
    });
    RigidBodySetPosition(memory, kBody, {10.f, -20.f, 30.f});
    RigidBodySetLinearVelocity(memory, kBody, {2.f, 0.f, 0.f});
    memory.WriteVec3BE(kFirst + 0x28, {2.f, -1.f, 0.5f});
    memory.WriteVec3BE(kSecond + 0x28, {-4.f, 1.f, 2.f});
    return memory;
}

void TestDirectLocalToWorldPreparation() {
    auto memory = Fixture();
    ExpectVector(WiiPrimitiveLocalPosition(memory.ReadOnly(), kFirst),
                 {2.f, -1.f, 0.5f});
    WiiRigidBodyPrimitivePrepare(memory, kFirst, kState);
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kFirst),
                 {11.5f, -17.f, 34.5f});
    WiiRigidBodyPrimitivePrepare(memory, kSecond, kState);
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kSecond),
                 {24.f, -7.f, 42.f});
    // Preparing a primitive must not alter local input or body pose.
    ExpectVector(WiiPrimitiveLocalPosition(memory.ReadOnly(), kFirst),
                 {2.f, -1.f, 0.5f});
    ExpectVector(RigidBodyPosition(memory.ReadOnly(), kBody),
                 {10.f, -20.f, 30.f});
}

void TestUsesExplicitStateArgument() {
    auto memory = Fixture(false);
    const std::uint32_t alternate_state = kBody + 0xB00u;
    memory.WriteVec3BE(alternate_state + 0x10, {100.f, 200.f, 300.f});
    memory.WriteMatrix4BE(alternate_state + 0x70, {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    });
    WiiRigidBodyPrimitivePrepare(memory, kFirst, alternate_state);
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kFirst),
                 {102.f, 199.f, 300.5f});
}

void TestFrameCallsPrepareBeforeIntegration() {
    auto memory = Fixture();
    const auto result = ApplyRigidBodyOnBeginFrame(
        memory, kBody, 0.5f, MakeWiiPrimitivePrepareCallback());
    assert(result.integration_called);
    assert(result.primitives_prepared == 2);
    assert(result.final_state_status == 0);
    assert(!result.gravity_applied);
    // BeginFrame prepares nodes before DoIntegration advances position.
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kFirst),
                 {11.5f, -17.f, 34.5f});
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kSecond),
                 {24.f, -7.f, 42.f});
    ExpectVector(RigidBodyPosition(memory.ReadOnly(), kBody),
                 {11.f, -20.f, 30.f});
}

void TestDisabledStatusSkipsPreparation() {
    auto memory = Fixture(true, 2);
    const auto result = ApplyRigidBodyOnBeginFrame(
        memory, kBody, 0.5f, MakeWiiPrimitivePrepareCallback());
    assert(!result.integration_called);
    assert(result.primitives_prepared == 0);
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kFirst),
                 {0.f,0.f,0.f});
    ExpectVector(RigidBodyPosition(memory.ReadOnly(), kBody),
                 {10.f,-20.f,30.f});
}

void TestDirectIncompleteOutputIsAtomic() {
    constexpr std::uint32_t primitive = 0x80070000u;
    constexpr std::uint32_t state = 0x80071000u;
    WiiMutableSnapshot sparse({
        {primitive, std::vector<std::uint8_t>(0x34, 0)},
        {state, std::vector<std::uint8_t>(0xB0, 0)}
    });
    sparse.WriteVec3BE(primitive + 0x28, {1.f,2.f,3.f});
    sparse.WriteMatrix4BE(state + 0x70, {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    });
    sparse.WriteVec3BE(state + 0x10, {100.f,200.f,300.f});
    MustThrow<std::out_of_range>([&] {
        WiiRigidBodyPrimitivePrepare(sparse, primitive, state);
    });
    ExpectVector(WiiPrimitiveLocalPosition(sparse.ReadOnly(), primitive),
                 {1.f,2.f,3.f});
}

void TestBadLaterPrimitiveRollsBackEarlierFrameWork() {
    auto memory = Fixture(false);
    // First primitive is valid and would receive a world position.
    // Its next pointer points to an unallocated second primitive.
    memory.WriteVec4BE(kState, {0.f,0.f,0.f,1.f});
    // node+0x00 is a raw big-endian next pointer; host snapshot can
    // encode it through two u16 writes.
    memory.WriteU16BE(kFirst, 0x9000u);
    memory.WriteU16BE(kFirst + 2, 0x0000u);
    const auto original_flags = RigidBodyFlags(memory.ReadOnly(), kBody);
    MustThrow<std::out_of_range>([&] {
        (void)ApplyRigidBodyOnBeginFrame(
            memory, kBody, 0.5f, MakeWiiPrimitivePrepareCallback());
    });
    assert(RigidBodyFlags(memory.ReadOnly(), kBody) == original_flags);
    ExpectVector(WiiPrimitivePreparedWorldPosition(memory.ReadOnly(), kFirst),
                 {0.f,0.f,0.f});
    ExpectVector(RigidBodyPosition(memory.ReadOnly(), kBody),
                 {10.f,-20.f,30.f});
}
} // namespace

int main() {
    TestDirectLocalToWorldPreparation();
    TestUsesExplicitStateArgument();
    TestFrameCallsPrepareBeforeIntegration();
    TestDisabledStatusSkipsPreparation();
    TestDirectIncompleteOutputIsAtomic();
    TestBadLaterPrimitiveRollsBackEarlierFrameWork();
}
