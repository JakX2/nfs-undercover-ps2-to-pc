#include "wii_rigidbody_drag.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {

std::uint32_t Add(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii DoDrag field address");
    return address + offset;
}

Vec3 ReadVec(const attrib::WiiAddressSpace& memory, std::uint32_t start) {
    return {ReadWiiF32(memory, start),
            ReadWiiF32(memory, Add(start, 4)),
            ReadWiiF32(memory, Add(start, 8))};
}

float WiiSqrtApprox(float squared) {
    // Original rsqrt(0x80232544) returns an approximation to sqrt,
    // taking the zero fallback unless the float compare exceeds
    // r2-24516, original IEEE-754 f32 bits 0x2E5BE6FF.
    constexpr float threshold = 5.00000006675716e-11f;
    return (squared > threshold) ? std::sqrt(squared) : 0.f;
}

float VectorMagnitude(Vec3 v) {
    const float square = std::fma(v.z, v.z,
                         std::fma(v.x, v.x, v.y * v.y));
    return WiiSqrtApprox(square);
}

float PairMagnitude(float a, float b) {
    return WiiSqrtApprox(std::fma(a, a, b * b));
}

Vec3 AngularDrag(Vec3 angular, Vec3 dimensions, Vec3 coefficients) {
    // Original angular drag 0x8030ED98..0x8030EFEC:
    //  (4 * length-axis) * sqrt(other-axis squares) per axis,
    //  then local angular component * area * environment coefficient.
    // The original squared angular magnitude calls rsqrt; its result
    // is scaled first by -0.5f and then by original air density 1.225f.
    // This host calculation preserves f32 steps, not exact PPC FPSCR.
    constexpr float four = 4.f;
    constexpr float minus_half = -0.5f;
    constexpr float density = 1.225000023841858f;
    const Vec3 areas{
        (four * dimensions.x) * PairMagnitude(dimensions.y, dimensions.z),
        (four * dimensions.y) * PairMagnitude(dimensions.x, dimensions.z),
        (four * dimensions.z) * PairMagnitude(dimensions.x, dimensions.y)
    };
    const float scale = (minus_half * VectorMagnitude(angular)) * density;
    return {
        ((angular.x * areas.x) * coefficients.x) * scale,
        ((angular.y * areas.y) * coefficients.y) * scale,
        ((angular.z * areas.z) * coefficients.z) * scale
    };
}

Vec3 LinearDrag(Vec3 velocity, Vec3 dimensions, Vec3 coefficients) {
    // Original linear drag 0x8030EFFC..0x8030F198:
    // projected area = 4 * (body length-axis)^2 per axis.
    // Force uses local velocity, its vector magnitude and density;
    // no body position translation in either virtual conversion.
    constexpr float four = 4.f;
    constexpr float minus_half = -0.5f;
    constexpr float density = 1.225000023841858f;
    const Vec3 areas{
        four * (dimensions.x * dimensions.x),
        four * (dimensions.y * dimensions.y),
        four * (dimensions.z * dimensions.z)
    };
    const float scale = (minus_half * VectorMagnitude(velocity)) * density;
    return {
        ((velocity.x * areas.x) * coefficients.x) * scale,
        ((velocity.y * areas.y) * coefficients.y) * scale,
        ((velocity.z * areas.z) * coefficients.z) * scale
    };
}

void Need(bool present, const char* reason) {
    if (!present) throw std::invalid_argument(reason);
}

} // namespace

WiiDragCallbacks MakeWiiBaseDragCallbacks(const WiiDetach& detach) {
    WiiDragCallbacks callbacks;
    callbacks.world_to_local = [](
        WiiMutableSnapshot& memory, std::uint32_t body, Vec3 vector) {
        return WiiRigidBodyBaseConvertWorldToLocal(
            memory.ReadOnly(), body, vector, false);
    };
    callbacks.local_to_world = [](
        WiiMutableSnapshot& memory, std::uint32_t body, Vec3 vector) {
        return WiiRigidBodyBaseConvertLocalToWorld(
            memory.ReadOnly(), body, vector, false);
    };
    callbacks.resolve_torque = [detach](
        WiiMutableSnapshot& memory, std::uint32_t body, Vec3 vector) {
        (void)WiiRigidBodyBaseResolveTorque(memory, body, vector, detach);
    };
    callbacks.resolve_force = [detach](
        WiiMutableSnapshot& memory, std::uint32_t body, Vec3 vector) {
        (void)WiiRigidBodyBaseResolveForce(memory, body, vector, detach);
    };
    return callbacks;
}

WiiDragResult ApplyRigidBodyDoDrag(
    WiiMutableSnapshot& snapshot, std::uint32_t body,
    const WiiDragCallbacks& callbacks) {
    // Keep original state address in a local, as PPC keeps r30 after
    // the initial body+0x70 -> wrapper+0x00 pointer chain.
    WiiMutableSnapshot next = snapshot;
    const auto first = next.ReadOnly();
    const auto state = RigidBodyStateAddress(first, body);
    const std::uint16_t initial_flags = RigidBodyFlags(first, body);
    WiiDragResult result{false, false, {0.f, 0.f, 0.f}, {0.f, 0.f, 0.f}};
    // Original 0x8030ED58: bit 0x0002 prevents BOTH drag sections.
    if ((initial_flags & 0x0002u) != 0) return result;

    if ((initial_flags & 0x0800u) != 0) {
        Need(static_cast<bool>(callbacks.world_to_local),
             "missing Wii virtual ConvertWorldToLocal callback");
        Need(static_cast<bool>(callbacks.local_to_world),
             "missing Wii virtual ConvertLocalToWorld callback");
        Need(static_cast<bool>(callbacks.resolve_torque),
             "missing Wii virtual ResolveTorque callback");

        // The angular vector is copied BEFORE the first virtual call.
        const Vec3 angular = ReadVec(next.ReadOnly(), Add(state, 0x30));
        const Vec3 local = callbacks.world_to_local(next, body, angular);
        const auto source = next.ReadOnly();
        const Vec3 dimensions = ReadVec(source, Add(body, 0xD4));
        const std::uint32_t environment = source.ReadU32BE(Add(body, 0x78));
        const Vec3 coeff = ReadVec(source, Add(environment, 0x60));
        const Vec3 local_torque = AngularDrag(local, dimensions, coeff);
        const Vec3 global_torque = callbacks.local_to_world(
            next, body, local_torque);
        callbacks.resolve_torque(next, body, global_torque);
        result.angular_path = true;
        result.world_torque = global_torque;
    }

    // Original 0x8030EFF0 uses lhz from the retained original state
    // pointer AFTER all first-path callbacks. Even if they change 0x0002,
    // only bit 0x0020 is tested here, unlike the initial early guard.
    const auto current_flags = next.ReadOnly().ReadU8(Add(state, 0x1C));
    const auto lower_flags = next.ReadOnly().ReadU8(Add(state, 0x1D));
    const std::uint16_t flags = std::uint16_t(
        (std::uint16_t(current_flags) << 8) | lower_flags);
    if ((flags & 0x0020u) != 0) {
        Need(static_cast<bool>(callbacks.world_to_local),
             "missing Wii virtual ConvertWorldToLocal callback");
        Need(static_cast<bool>(callbacks.local_to_world),
             "missing Wii virtual ConvertLocalToWorld callback");
        Need(static_cast<bool>(callbacks.resolve_force),
             "missing Wii virtual ResolveForce callback");

        const Vec3 velocity = ReadVec(next.ReadOnly(), Add(state, 0x20));
        const Vec3 local = callbacks.world_to_local(next, body, velocity);
        const auto source = next.ReadOnly();
        const Vec3 dimensions = ReadVec(source, Add(body, 0xD4));
        const std::uint32_t environment = source.ReadU32BE(Add(body, 0x78));
        const Vec3 coeff = ReadVec(source, Add(environment, 0x70));
        const Vec3 local_force = LinearDrag(local, dimensions, coeff);
        const Vec3 global_force = callbacks.local_to_world(
            next, body, local_force);
        callbacks.resolve_force(next, body, global_force);
        result.linear_path = true;
        result.world_force = global_force;
    }

    snapshot = std::move(next);
    return result;
}

} // namespace undercover::vehicle
