#include "wii_rigidbody_drag.hpp"
#include "wii_rigidbody_endframe.hpp"
#include "wii_rigidbody_frame.hpp"
#include "wii_rigidbody_sleep.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t body = 0x80060000u;
constexpr std::uint32_t state = body + 0x400u;
constexpr std::uint32_t environment = body + 0x800u;

void Put32(std::vector<std::uint8_t>& bytes, std::size_t offset, std::uint32_t value) {
    assert(offset + 4 <= bytes.size());
    bytes[offset] = std::uint8_t(value >> 24);
    bytes[offset + 1] = std::uint8_t(value >> 16);
    bytes[offset + 2] = std::uint8_t(value >> 8);
    bytes[offset + 3] = std::uint8_t(value);
}
void PutF32(std::vector<std::uint8_t>& bytes, std::size_t offset, float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    Put32(bytes, offset, bits);
}
bool Near(float a, float b, float tolerance=0.001f) {
    return std::abs(a - b) < tolerance;
}
bool IsZero(Vec3 v) {
    return v.x == 0 && v.y == 0 && v.z == 0;
}
WiiMutableSnapshot Fixture() {
    std::vector<std::uint8_t> bytes(0x1200, 0);
    Put32(bytes, 0x70, body + 0x200);          // Wii wrapper
    Put32(bytes, 0x200, state);               // Wii physics state
    Put32(bytes, 0x78, environment);          // Wii physics environment
    Put32(bytes, 0x104, body + 0x104);        // empty primitive-list sentinel
    bytes[0x400 + 0x1C] = 0x08;                // state flags 0x0820
    bytes[0x400 + 0x1D] = 0x20;
    PutF32(bytes, 0x400 + 0x2C, 100.f);        // mass
    PutF32(bytes, 0x400 + 0x3C, 0.01f);        // inverse mass
    PutF32(bytes, 0x400 + 0x6C, 2.f);          // radius
    PutF32(bytes, 0x800 + 0xE0, 0.f);          // sleep threshold: never sleep
    WiiMutableSnapshot m({{body, std::move(bytes)}});

    const WiiMatrix4 identity{
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    };
    m.WriteVec4BE(state, {0.f,0.f,0.f,1.f});
    m.WriteVec3BE(state + 0x40, {1.f,1.f,1.f}); // inertia reciprocal inputs
    m.WriteMatrix4BE(state + 0x70, identity);
    m.WriteMatrix4BE(body + 0x84, identity);
    m.WriteVec3BE(body + 0xD4, {1.f,2.f,3.f});
    m.WriteVec3BE(environment + 0x60, {1.f,1.f,1.f});
    m.WriteVec3BE(environment + 0x70, {1.f,1.f,1.f});
    RigidBodySetLinearVelocity(m, body, {3.f,4.f,0.f});
    RigidBodySetAngularVelocity(m, body, {0.f,3.f,4.f});
    return m;
}

void TestBeginEndFrameForcePipeline() {
    auto memory = Fixture();
    int detaches = 0;
    const WiiDragCallbacks drag = MakeWiiBaseDragCallbacks(
        [&](WiiMutableSnapshot& snapshot, std::uint32_t target) {
            ++detaches;
            assert(target == body);
            assert(snapshot.ReadOnly().ReadU8(state + 0x5D) == 0);
        });

    WiiEndFrameCallbacks callbacks;
    callbacks.do_drag = [&](WiiMutableSnapshot& snapshot, std::uint32_t target) {
        const auto result = ApplyRigidBodyDoDrag(snapshot, target, drag);
        assert(result.angular_path && result.linear_path);
    };
    callbacks.should_sleep = [](WiiMutableSnapshot& snapshot, std::uint32_t target) {
        return WiiRigidBodyBaseShouldSleep(snapshot.ReadOnly(), target);
    };
    const auto start = RigidBodyVelocity(memory.ReadOnly(), body);
    assert(Near(start.x, 3.f) && Near(start.y, 4.f));

    // At time zero no pending force exists. Frame begin prepares and
    // integrates but must NOT invent aerodynamic drag before OnEndFrame.
    const auto begin1 = ApplyRigidBodyOnBeginFrame(memory, body, 0.25f);
    assert(begin1.integration_called && !begin1.gravity_applied);
    assert(IsZero(RigidBodyForce(memory.ReadOnly(), body)));
    const auto before_drag = RigidBodyVelocity(memory.ReadOnly(), body);
    assert(Near(before_drag.x, 3.f) && Near(before_drag.y, 4.f));
    assert((RigidBodyFlags(memory.ReadOnly(), body) & 0x0400u) != 0);

    const auto end1 = ApplyRigidBodyOnEndFrame(memory, body, 0.25f, false, callbacks);
    assert(end1.drag_dispatched && !end1.collider_updated);
    assert(!end1.entered_sleeping_state && end1.exit_status == 0);
    assert((end1.exit_flags & 0x0400u) == 0);
    assert(detaches == 2);
    const Vec3 queued_force = RigidBodyForce(memory.ReadOnly(), body);
    const Vec3 queued_torque = RigidBodyTorque(memory.ReadOnly(), body);
    assert(Near(queued_force.x, -36.75f, 0.04f));
    assert(Near(queued_force.y, -196.f, 0.07f));
    assert(queued_torque.y < -200.f && queued_torque.z < -300.f);
    assert(Near(RigidBodyVelocity(memory.ReadOnly(), body).x, 3.f));

    // Frame two consumes the force from the PREVIOUS end-of-frame,
    // applies mass/timestep integration, then clears both accumulators.
    const auto begin2 = ApplyRigidBodyOnBeginFrame(memory, body, 0.25f);
    assert(begin2.integration_called && !begin2.gravity_applied);
    const auto after = RigidBodyVelocity(memory.ReadOnly(), body);
    const float expected_x = std::fma(-36.75f, 0.25f * 0.01f, 3.f);
    const float expected_y = std::fma(-196.f, 0.25f * 0.01f, 4.f);
    assert(Near(after.x, expected_x, 0.002f));
    assert(Near(after.y, expected_y, 0.002f));
    assert(IsZero(RigidBodyForce(memory.ReadOnly(), body)));
    assert(IsZero(RigidBodyTorque(memory.ReadOnly(), body)));
    assert(detaches == 2); // integration does not invoke drag/Detach

    const auto end2 = ApplyRigidBodyOnEndFrame(memory, body, 0.25f, false, callbacks);
    assert(end2.drag_dispatched && end2.exit_status == 0);
    assert(detaches == 4);
    assert(RigidBodyForce(memory.ReadOnly(), body).x < 0.f);
    assert(RigidBodyForce(memory.ReadOnly(), body).y < 0.f);
}

void TestInitialDragInhibitDoesNotInventForce() {
    auto memory = Fixture();
    // Original bit 0x0002 enables gravity in begin frame and suppresses
    // BOTH drag paths in DoDrag. OnEndFrame still dispatches DoDrag.
    memory.WriteU16BE(state + 0x1C, 0x0822u);
    int detaches = 0;
    const auto drag = MakeWiiBaseDragCallbacks(
        [&](WiiMutableSnapshot&, std::uint32_t) { ++detaches; });
    WiiEndFrameCallbacks callbacks;
    callbacks.do_drag = [drag](WiiMutableSnapshot& m, std::uint32_t target) {
        const auto result = ApplyRigidBodyDoDrag(m, target, drag);
        assert(!result.angular_path && !result.linear_path);
    };
    callbacks.should_sleep = [](WiiMutableSnapshot&, std::uint32_t) {
        return false;
    };
    const auto begin = ApplyRigidBodyOnBeginFrame(memory, body, 0.25f);
    assert(begin.gravity_applied);
    const auto force_y = RigidBodyForce(memory.ReadOnly(), body).y;
    assert(force_y == 0.f); // environment gravity in fixture is zero
    const auto end = ApplyRigidBodyOnEndFrame(memory, body, 0.25f, false, callbacks);
    assert(end.drag_dispatched && detaches == 0);
    assert(IsZero(RigidBodyForce(memory.ReadOnly(), body)));
}
} // namespace

int main() {
    TestBeginEndFrameForcePipeline();
    TestInitialDragInhibitDoesNotInventForce();
}
