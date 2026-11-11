#include "wii_rigidbody_drag.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;
constexpr std::uint32_t kEnvironment = kBody + 0x800u;

void Set32(std::vector<std::uint8_t>& b, std::size_t offset, std::uint32_t value) {
    assert(offset + 4 <= b.size());
    b[offset] = std::uint8_t(value >> 24);
    b[offset + 1] = std::uint8_t(value >> 16);
    b[offset + 2] = std::uint8_t(value >> 8);
    b[offset + 3] = std::uint8_t(value);
}
void CheckNear(float actual, float expected, float tol=0.03f) {
    assert(std::abs(actual - expected) <= tol);
}
void CheckVec(Vec3 actual, Vec3 expected, float tol=0.03f) {
    CheckNear(actual.x, expected.x, tol);
    CheckNear(actual.y, expected.y, tol);
    CheckNear(actual.z, expected.z, tol);
}
template <typename E, typename F> void ExpectThrow(F f) {
    bool threw = false;
    try { f(); } catch (const E&) { threw = true; }
    assert(threw);
}

WiiMutableSnapshot Fixture(std::uint16_t flags=0x0820u,
                           bool valid_environment=true) {
    std::vector<std::uint8_t> bytes(0xA00, 0);
    Set32(bytes, 0x70, kBody + 0x200);
    Set32(bytes, 0x200, kState);
    Set32(bytes, 0x78, valid_environment ? kEnvironment : 0);
    bytes[0x400 + 0x1C] = std::uint8_t(flags >> 8);
    bytes[0x400 + 0x1D] = std::uint8_t(flags);
    WiiMutableSnapshot m({{kBody, std::move(bytes)}});
    m.WriteMatrix4BE(kState + 0x70, {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    });
    m.WriteVec3BE(kBody + 0xD4, {1.f, 2.f, 3.f});
    m.WriteVec3BE(kEnvironment + 0x60, {1.f, 1.f, 1.f});
    m.WriteVec3BE(kEnvironment + 0x70, {1.f, 1.f, 1.f});
    RigidBodySetAngularVelocity(m, kBody, {0.f, 3.f, 4.f});
    RigidBodySetLinearVelocity(m, kBody, {3.f, 4.f, 0.f});
    return m;
}

void TestBothDragPathsUsingBaseMethods() {
    auto m = Fixture();
    int detaches = 0;
    const auto callbacks = MakeWiiBaseDragCallbacks(
        [&](WiiMutableSnapshot& state, std::uint32_t body) {
            assert(body == kBody);
            ++detaches;
            assert(state.ReadOnly().ReadU8(kState + 0x5D) == 0);
            assert((RigidBodyFlags(state.ReadOnly(), body) & 0x0040u) != 0);
        });
    const auto result = ApplyRigidBodyDoDrag(m, kBody, callbacks);
    assert(result.angular_path && result.linear_path);
    assert(detaches == 2);
    CheckVec(result.world_torque, {0.f, -232.4274f, -328.7020f}, 0.1f);
    CheckVec(result.world_force, {-36.75f, -196.f, 0.f}, 0.06f);
    CheckVec(RigidBodyTorque(m.ReadOnly(), kBody), result.world_torque);
    CheckVec(RigidBodyForce(m.ReadOnly(), kBody), result.world_force);
    assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x0860u);
    CheckVec(RigidBodyVelocity(m.ReadOnly(), kBody), {3.f, 4.f, 0.f});
    CheckVec(RigidBodyAngularVelocity(m.ReadOnly(), kBody), {0.f, 3.f, 4.f});
}

void TestEachGateAndGlobalEarlyReturn() {
    int calls = 0;
    WiiDragCallbacks callbacks;
    callbacks.world_to_local = [&](WiiMutableSnapshot&, std::uint32_t, Vec3 input) {
        ++calls;
        return input;
    };
    callbacks.local_to_world = [&](WiiMutableSnapshot&, std::uint32_t, Vec3 input) {
        ++calls;
        return input;
    };
    callbacks.resolve_torque = [&](WiiMutableSnapshot&, std::uint32_t, Vec3) {
        ++calls;
    };
    callbacks.resolve_force = [&](WiiMutableSnapshot&, std::uint32_t, Vec3) {
        ++calls;
    };
    for (const auto& tc : {
        std::pair<std::uint16_t, int>{0x0000, 0},
        {0x0800, 3},
        {0x0020, 3},
        {0x0820, 6},
        {0x0822, 0},
        {0x0802, 0},
        {0x0022, 0}
    }) {
        auto m = Fixture(tc.first);
        calls = 0;
        const auto result = ApplyRigidBodyDoDrag(m, kBody, callbacks);
        assert(calls == tc.second);
        assert(result.angular_path == (tc.second >= 3 && (tc.first & 0x0800u)));
        assert(result.linear_path == (tc.second >= 3 && (tc.first & 0x0020u)));
        assert(RigidBodyFlags(m.ReadOnly(), kBody) == tc.first);
    }
}

void TestSecondGateIsReadAfterTorqueCallback() {
    auto m = Fixture(0x0800);
    std::vector<std::string> order;
    WiiDragCallbacks cb;
    cb.world_to_local = [&](WiiMutableSnapshot&, std::uint32_t, Vec3 v) {
        order.emplace_back("to_local");
        return v;
    };
    cb.local_to_world = [&](WiiMutableSnapshot&, std::uint32_t, Vec3 v) {
        order.emplace_back("to_world");
        return v;
    };
    cb.resolve_torque = [&](WiiMutableSnapshot& memory, std::uint32_t, Vec3) {
        order.emplace_back("torque");
        // The source PPC re-loads +0x1C after this call. A newly added
        // bit 0x0020 activates the second path, even though it was absent
        // at entry. Also setting 0x0002 HERE does not repeat the top guard.
        memory.WriteU16BE(kState + 0x1C, 0x0822);
    };
    cb.resolve_force = [&](WiiMutableSnapshot&, std::uint32_t, Vec3) {
        order.emplace_back("force");
    };
    const auto result = ApplyRigidBodyDoDrag(m, kBody, cb);
    assert(result.angular_path && result.linear_path);
    assert((order == std::vector<std::string>{
        "to_local", "to_world", "torque",
        "to_local", "to_world", "force"
    }));
    assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x0822);
}

void TestMissingCallbacksAndInvalidSourceAreAtomic() {
    auto m = Fixture(0x0800u);
    ExpectThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyDoDrag(m, kBody, {});
    });
    assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x0800u);
    CheckVec(RigidBodyTorque(m.ReadOnly(), kBody), {0, 0, 0});

    WiiDragCallbacks cb = MakeWiiBaseDragCallbacks(
        [](WiiMutableSnapshot&, std::uint32_t) {});
    cb.local_to_world = [](WiiMutableSnapshot& copy, std::uint32_t, Vec3) -> Vec3 {
        copy.WriteU16BE(kState + 0x1C, 0xFFFFu);
        throw std::logic_error("host callback failed");
    };
    ExpectThrow<std::logic_error>([&] {
        (void)ApplyRigidBodyDoDrag(m, kBody, cb);
    });
    assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x0800u);
    CheckVec(RigidBodyTorque(m.ReadOnly(), kBody), {0, 0, 0});

    auto bad = Fixture(0x0020u, false);
    ExpectThrow<std::out_of_range>([&] {
        (void)ApplyRigidBodyDoDrag(bad, kBody, MakeWiiBaseDragCallbacks(
            [](WiiMutableSnapshot&, std::uint32_t) {}));
    });
    assert(RigidBodyFlags(bad.ReadOnly(), kBody) == 0x0020u);
}

void TestZeroDragStillCallsVirtuals() {
    auto m = Fixture(0x0820u);
    m.WriteVec3BE(kEnvironment + 0x60, {0, 0, 0});
    m.WriteVec3BE(kEnvironment + 0x70, {0, 0, 0});
    int detaches = 0;
    auto r = ApplyRigidBodyDoDrag(m, kBody, MakeWiiBaseDragCallbacks(
        [&](WiiMutableSnapshot&, std::uint32_t) { ++detaches; }));
    assert(r.angular_path && r.linear_path);
    assert(detaches == 2);
    CheckVec(r.world_torque, {0, 0, 0});
    CheckVec(r.world_force, {0, 0, 0});
}
} // namespace

int main() {
    TestBothDragPathsUsingBaseMethods();
    TestEachGateAndGlobalEarlyReturn();
    TestSecondGateIsReadAfterTorqueCallback();
    TestMissingCallbacksAndInvalidSourceAreAtomic();
    TestZeroDragStillCallsVirtuals();
}
