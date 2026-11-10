#include "wii_rigidbody_frame.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t body = 0x80060000u;
constexpr std::uint32_t state = body + 0x400u;
constexpr std::uint32_t sentinel = body + 0x104u;

void Set32(std::vector<std::uint8_t>& bytes, std::size_t at, std::uint32_t v) {
    assert(at + 4 <= bytes.size());
    bytes[at] = std::uint8_t(v >> 24);
    bytes[at+1] = std::uint8_t(v >> 16);
    bytes[at+2] = std::uint8_t(v >> 8);
    bytes[at+3] = std::uint8_t(v);
}
void SetF32(std::vector<std::uint8_t>& bytes, std::size_t at, float f) {
    std::uint32_t bits;
    static_assert(sizeof(bits) == sizeof(f), "f32 required");
    std::memcpy(&bits, &f, sizeof(bits));
    Set32(bytes, at, bits);
}
template <class Error, class Fn> void MustThrow(Fn callback) {
    bool happened = false;
    try { callback(); } catch (const Error&) { happened = true; }
    assert(happened);
}
bool Near(float a, float b, float tolerance=0.0002f) {
    return std::abs(a-b) < tolerance;
}
WiiMutableSnapshot Fixture(std::uint8_t status=0, std::uint16_t flags=2,
                           bool two_primitives=false, bool cyclic=false) {
    std::vector<std::uint8_t> bytes(0x900, 0);
    Set32(bytes, 0x70, body + 0x200);
    Set32(bytes, 0x200, state);
    Set32(bytes, 0x78, body + 0x700); // environment/gravity settings
    SetF32(bytes, 0x700 + 0xF0, -9.8f);
    SetF32(bytes, 0x400 + 0x2c, 1000.f);
    SetF32(bytes, 0x400 + 0x3c, .001f);
    SetF32(bytes, 0x400 + 0x40, 1.f);
    SetF32(bytes, 0x400 + 0x44, 1.f);
    SetF32(bytes, 0x400 + 0x48, 1.f);
    bytes[0x400 + 0x1c] = std::uint8_t(flags >> 8);
    bytes[0x400 + 0x1d] = std::uint8_t(flags);
    bytes[0x400 + 0x1e] = 0xBE;
    bytes[0x400 + 0x1f] = 0xEF;
    bytes[0x400 + 0x5d] = status;
    Set32(bytes, 0x104, two_primitives ? body + 0x300 : sentinel);
    if (two_primitives) {
        Set32(bytes, 0x300, cyclic ? body + 0x300 : body + 0x320);
        Set32(bytes, 0x320, sentinel);
    }
    WiiMutableSnapshot result({{body, std::move(bytes)}});
    const WiiMatrix4 identity{
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1
    };
    result.WriteVec4BE(state, {0,0,0,1});
    result.WriteMatrix4BE(state+0x70, identity);
    result.WriteMatrix4BE(body+0x84, identity);
    return result;
}

void TestGravityCarriedToNextFrame() {
    auto s = Fixture();
    RigidBodySetForce(s, body, {0.f, -9800.f, 0.f});
    RigidBodySetTorque(s, body, {3.f, 4.f, 5.f});
    const auto result = ApplyRigidBodyOnBeginFrame(s, body, 0.1f);
    assert(result.integration_called);
    assert(result.primitives_prepared == 0);
    assert(result.gravity_applied && result.final_state_status == 0);
    const auto v = RigidBodyVelocity(s.ReadOnly(), body);
    const auto p = RigidBodyPosition(s.ReadOnly(), body);
    assert(Near(v.y, -0.98f));
    assert(Near(p.y, -0.098f));
    assert(Near(RigidBodyForce(s.ReadOnly(), body).y, -9800.f, 0.001f));
    const auto torque = RigidBodyTorque(s.ReadOnly(), body);
    assert(torque.x == 0 && torque.y == 0 && torque.z == 0);
    assert(RigidBodyFlags(s.ReadOnly(), body) == 0x0402u);
    assert(s.ReadOnly().ReadU8(state+0x1e) == 0x04);
    assert(s.ReadOnly().ReadU8(state+0x1f) == 0x02);

    // The same pending gravity force should be consumed during the next
    // frame and restored as a next-frame accumulator.
    (void)ApplyRigidBodyOnBeginFrame(s, body, 0.1f);
    const auto again = RigidBodyVelocity(s.ReadOnly(), body);
    assert(Near(again.y, -1.96f));
    assert(Near(RigidBodyForce(s.ReadOnly(), body).y, -9800.f, 0.001f));
}

void TestModelingOffSkipsIntegrationButClearsAccumulators() {
    auto s = Fixture(2);
    RigidBodySetPosition(s, body, {11,12,13});
    RigidBodySetLinearVelocity(s, body, {4,5,6});
    RigidBodySetForce(s, body, {10,20,30});
    RigidBodySetTorque(s, body, {1,2,3});
    auto r = ApplyRigidBodyOnBeginFrame(s, body, 1.f);
    assert(!r.integration_called && r.primitives_prepared == 0);
    assert(!r.gravity_applied && r.final_state_status == 2);
    assert(RigidBodyPosition(s.ReadOnly(), body).x == 11);
    assert(RigidBodyVelocity(s.ReadOnly(), body).y == 5);
    assert(RigidBodyForce(s.ReadOnly(), body).x == 0);
    assert(RigidBodyForce(s.ReadOnly(), body).y == 0);
    assert(RigidBodyTorque(s.ReadOnly(), body).z == 0);
    assert(RigidBodyFlags(s.ReadOnly(), body) == 0x0402);
    assert(s.ReadOnly().ReadU8(state+0x1e) == 0xBE);
    assert(s.ReadOnly().ReadU8(state+0x1f) == 0xEF);
}

void TestSleepingStillInvokesIntegrationClear() {
    auto s = Fixture(1, 0);
    RigidBodySetLinearVelocity(s, body, {4,5,6});
    RigidBodySetAngularVelocity(s, body, {1,2,3});
    RigidBodySetForce(s, body, {1,2,3});
    const auto r = ApplyRigidBodyOnBeginFrame(s, body, .25f);
    assert(r.integration_called && !r.gravity_applied);
    const auto v = RigidBodyVelocity(s.ReadOnly(), body);
    const auto w = RigidBodyAngularVelocity(s.ReadOnly(), body);
    assert(v.x == 0 && v.y == 0 && v.z == 0);
    assert(w.x == 0 && w.y == 0 && w.z == 0);
    assert(RigidBodyForce(s.ReadOnly(), body).y == 0);
}

void TestPrimitivePrepareChain() {
    auto s = Fixture(0, 0, true);
    int callbacks = 0;
    auto r = ApplyRigidBodyOnBeginFrame(s, body, 1.f,
        [&](WiiMutableSnapshot& snapshot, std::uint32_t node, std::uint32_t state_ptr) {
            assert(state_ptr == state);
            assert(node == body+0x300 || node == body+0x320);
            ++callbacks;
            auto f = RigidBodyForce(snapshot.ReadOnly(), body);
            f.x += 1000.f;
            RigidBodySetForce(snapshot, body, f);
        });
    assert(callbacks == 2 && r.primitives_prepared == 2);
    assert(r.integration_called && !r.gravity_applied);
    assert(Near(RigidBodyVelocity(s.ReadOnly(), body).x, 2.f));
    assert(Near(RigidBodyPosition(s.ReadOnly(), body).x, 2.f));
    assert(RigidBodyForce(s.ReadOnly(), body).x == 0.f);
}

void TestInvalidListIsTransactional() {
    auto cyclic = Fixture(0, 0, true, true);
    const auto original_flags = RigidBodyFlags(cyclic.ReadOnly(), body);
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnBeginFrame(cyclic, body, 1.f,
            [&](WiiMutableSnapshot& s, std::uint32_t, std::uint32_t) {
                RigidBodySetForce(s, body, {1000.f,0.f,0.f});
            });
    });
    assert(RigidBodyFlags(cyclic.ReadOnly(), body) == original_flags);
    assert(RigidBodyForce(cyclic.ReadOnly(), body).x == 0.f);

    auto no_callback = Fixture(0, 0, true);
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnBeginFrame(no_callback, body, 1.f);
    });
    assert(RigidBodyFlags(no_callback.ReadOnly(), body) == 0);
    assert(RigidBodyVelocity(no_callback.ReadOnly(), body).x == 0.f);
}
} // namespace

int main() {
    TestGravityCarriedToNextFrame();
    TestModelingOffSkipsIntegrationButClearsAccumulators();
    TestSleepingStillInvokesIntegrationClear();
    TestPrimitivePrepareChain();
    TestInvalidListIsTransactional();
}
