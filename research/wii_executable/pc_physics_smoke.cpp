// Minimal native C++17 PC-host executable for the source-only Wii physics
// reconstruction. It uses entirely synthetic state and NO original assets.
// It is a command-line regression/smoke demonstration, NOT a game port.
#include "wii_rigidbody_detach.hpp"
#include "wii_rigidbody_drag.hpp"
#include "wii_rigidbody_endframe.hpp"
#include "wii_rigidbody_frame.hpp"
#include "wii_rigidbody_primitive.hpp"
#include "wii_rigidbody_sleep.hpp"

#include <cmath>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace undercover::vehicle;

constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400u;
constexpr std::uint32_t kEnvironment = kBody + 0x800u;
constexpr std::uint32_t kPrimitive = kBody + 0x900u;
constexpr std::uint32_t kSentinel = kBody + 0x104u;
constexpr float kDt = 0.1f;
constexpr float kInverseMass = 0.01f;

void Put32(std::vector<std::uint8_t>& bytes,
           std::size_t offset, std::uint32_t value) {
    if (offset > bytes.size() || bytes.size() - offset < 4u)
        throw std::out_of_range("synthetic Wii pointer write out of range");
    bytes[offset] = static_cast<std::uint8_t>(value >> 24);
    bytes[offset + 1] = static_cast<std::uint8_t>(value >> 16);
    bytes[offset + 2] = static_cast<std::uint8_t>(value >> 8);
    bytes[offset + 3] = static_cast<std::uint8_t>(value);
}

void PutF32(std::vector<std::uint8_t>& bytes,
            std::size_t offset, float value) {
    static_assert(sizeof(float) == sizeof(std::uint32_t),
                  "host IEEE-754 float32 required");
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, 4);
    Put32(bytes, offset, bits);
}

WiiMutableSnapshot MakeSyntheticBody() {
    std::vector<std::uint8_t> bytes(0x1200, 0);
    // Original Wii object layout verified from PowerPC accessors.
    Put32(bytes, 0x70, kBody + 0x200); // body -> wrapper
    Put32(bytes, 0x200, kState);       // wrapper -> physics state
    Put32(bytes, 0x78, kEnvironment);  // body -> environment
    Put32(bytes, 0x104, kPrimitive); // first real primitive in list
    Put32(bytes, 0x900, kSentinel); // primitive next points to sentinel
    PutF32(bytes, 0x900 + 0x28, 1.f); // local primitive X
    PutF32(bytes, 0x900 + 0x2C, 0.f); // local primitive Y
    PutF32(bytes, 0x900 + 0x30, 0.f); // local primitive Z
    // Drag enabled on both source-backed flag gates. No attach/gravity bit.
    bytes[0x400 + 0x1C] = 0x08;
    bytes[0x400 + 0x1D] = 0x20;
    PutF32(bytes, 0x400 + 0x2C, 100.f);      // mass
    PutF32(bytes, 0x400 + 0x3C, kInverseMass);
    PutF32(bytes, 0x400 + 0x6C, 2.f);        // radius
    PutF32(bytes, 0x800 + 0xE0, 0.f);        // never choose sleep branch

    WiiMutableSnapshot memory({{kBody, std::move(bytes)}});
    const WiiMatrix4 identity{
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    };
    memory.WriteVec4BE(kState, {0.f,0.f,0.f,1.f});
    memory.WriteVec3BE(kState + 0x40, {1.f,1.f,1.f});
    memory.WriteMatrix4BE(kState + 0x70, identity);
    memory.WriteMatrix4BE(kBody + 0x84, identity);
    memory.WriteVec3BE(kBody + 0xD4, {1.f,2.f,3.f});
    memory.WriteVec3BE(kEnvironment + 0x60, {1.f,1.f,1.f});
    memory.WriteVec3BE(kEnvironment + 0x70, {1.f,1.f,1.f});
    RigidBodySetLinearVelocity(memory, kBody, {3.f,4.f,0.f});
    RigidBodySetAngularVelocity(memory, kBody, {0.f,3.f,4.f});
    return memory;
}

float Dot(Vec3 a, Vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

void Require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

bool Near(float actual, float expected, float tolerance=0.003f) {
    return std::isfinite(actual) && std::isfinite(expected) &&
           std::abs(actual - expected) < tolerance;
}

int ParseFrames(int argc, char** argv) {
    if (argc == 1) return 2;
    if (argc != 3 || std::string(argv[1]) != "--steps")
        throw std::invalid_argument("usage: nfsuc_physics_smoke [--steps 1..20]");
    std::size_t parsed = 0;
    const std::string arg = argv[2];
    const int frames = std::stoi(arg, &parsed);
    if (parsed != arg.size() || frames < 1 || frames > 20)
        throw std::invalid_argument("steps must be a whole number from 1 to 20");
    return frames;
}

int Run(int steps) {
    auto memory = MakeSyntheticBody();
    int detach_calls = 0;
    const WiiDetach detach = [&](WiiMutableSnapshot& snapshot,
                                 std::uint32_t rigid_body) {
        // The owner's original base Detach is now reconstructed.
        // With synthetic flags 0x0820 / 0x0860 its bit 0x0002 gate
        // takes the proven early no-op branch. No owner callback is needed.
        const auto result = WiiRigidBodyBaseDetach(snapshot, rigid_body, {});
        Require(!result.cleared_attached_flag,
                "unexpected attached-owner branch in synthetic fixture");
        ++detach_calls;
    };

    const WiiDragCallbacks drag = MakeWiiBaseDragCallbacks(detach);
    WiiEndFrameCallbacks end;
    end.do_drag = [&](WiiMutableSnapshot& snapshot, std::uint32_t body) {
        const auto result = ApplyRigidBodyDoDrag(snapshot, body, drag);
        Require(result.angular_path && result.linear_path,
                "expected both drag branches");
    };
    end.should_sleep = [](WiiMutableSnapshot& snapshot, std::uint32_t body) {
        return WiiRigidBodyBaseShouldSleep(snapshot.ReadOnly(), body);
    };

    Vec3 previous_velocity = RigidBodyVelocity(memory.ReadOnly(), kBody);
    Vec3 pending_force{0.f,0.f,0.f};
    std::cout << "frame,position_x,position_y,position_z,"
                 "velocity_x,velocity_y,velocity_z,"
                 "queued_force_x,queued_force_y,queued_force_z,"
                 "prepared_primitive_x,prepared_primitive_y,prepared_primitive_z\n";
    std::cout << std::fixed << std::setprecision(6);
    for (int frame = 1; frame <= steps; ++frame) {
        // The original prepares primitives BEFORE integrating the body.
        const Vec3 expected_primitive = WiiRigidBodyBaseConvertLocalToWorld(
            memory.ReadOnly(), kBody, {1.f,0.f,0.f}, true);
        const auto begin = ApplyRigidBodyOnBeginFrame(
            memory, kBody, kDt, MakeWiiPrimitivePrepareCallback());
        Require(begin.integration_called && begin.primitives_prepared == 1 &&
                !begin.gravity_applied,
                "unexpected Wii begin-frame/primitive branch");
        const Vec3 prepared = WiiPrimitivePreparedWorldPosition(
            memory.ReadOnly(), kPrimitive);
        Require(Near(prepared.x, expected_primitive.x) &&
                Near(prepared.y, expected_primitive.y) &&
                Near(prepared.z, expected_primitive.z),
                "primitive not prepared at the original pre-integration pose");
        const auto velocity = RigidBodyVelocity(memory.ReadOnly(), kBody);
        Require(Near(velocity.x,
                     std::fma(pending_force.x, kDt * kInverseMass,
                              previous_velocity.x)) &&
                Near(velocity.y,
                     std::fma(pending_force.y, kDt * kInverseMass,
                              previous_velocity.y)) &&
                Near(velocity.z,
                     std::fma(pending_force.z, kDt * kInverseMass,
                              previous_velocity.z)),
                "queued force was not integrated in the following frame");
        const auto force_after_begin = RigidBodyForce(memory.ReadOnly(), kBody);
        Require(force_after_begin.x == 0.f && force_after_begin.y == 0.f &&
                force_after_begin.z == 0.f,
                "force accumulator was not cleared by begin-frame");

        const auto ended = ApplyRigidBodyOnEndFrame(
            memory, kBody, kDt, false, end);
        Require(ended.drag_dispatched && !ended.collider_updated &&
                ended.exit_status == 0,
                "unexpected Wii end-frame branch");
        const auto snapshot = memory.ReadOnly();
        const auto force = RigidBodyForce(snapshot, kBody);
        const auto position = RigidBodyPosition(snapshot, kBody);
        Require(std::isfinite(Dot(force, velocity)) &&
                Dot(force, velocity) < -0.001f,
                "aerodynamic force is not opposing movement");
        Require(std::isfinite(position.x) &&
                std::isfinite(position.y) &&
                std::isfinite(position.z), "invalid position");
        Require((RigidBodyFlags(snapshot, kBody) & 0x0400u) == 0,
                "end-frame failed to clear processing flag");
        std::cout << frame << "," << position.x << "," << position.y << ","
                  << position.z << "," << velocity.x << ","
                  << velocity.y << "," << velocity.z << ","
                  << force.x << "," << force.y << "," << force.z << ","
                  << prepared.x << "," << prepared.y << "," << prepared.z << "\n";
        previous_velocity = velocity;
        pending_force = force;
    }
    Require(detach_calls == 2 * steps,
            "expected two original Resolve calls per synthetic frame");
    std::cerr << "PASS: native C++ physics smoke test ("
              << steps << " synthetic frames)\n";
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    try {
        return Run(ParseFrames(argc, argv));
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << "\n";
        return 1;
    }
}
