#pragma once

#include "wii_rigidbody_primitive.hpp"
#include "wii_rigidbody_orientation.hpp"

#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>

namespace undercover::vehicle {

// Original Wii Primitive::SetCollision at 0x8030BD5C, 0x1EC bytes.
// These are its verified inputs to Geometry::Set, NOT a reconstruction
// of Geometry::Set or contact generation. Owner binaries remain private.
struct WiiPrimitiveCollisionCall {
    WiiMatrix4 orientation;
    Vec3 world_position;
    Vec3 primitive_parameters;    // Primitive +0x18,+0x1C,+0x20.
    Vec3 world_delta;             // New position minus Prepare's +0x38.
    std::uint32_t shape;          // Primitive +0x24.
    bool uses_identity_orientation;
};

inline WiiPrimitiveCollisionCall BuildWiiPrimitiveCollisionCall(
    const attrib::WiiAddressSpace& memory, std::uint32_t primitive,
    std::uint32_t state) {
    const auto at = [](std::uint32_t base, std::uint32_t offset) {
        if (!base || base > std::numeric_limits<std::uint32_t>::max() - offset)
            throw std::out_of_range("invalid Wii collision argument address");
        return base + offset;
    };
    const auto vec = [&](std::uint32_t base) -> Vec3 {
        return {ReadWiiF32(memory, base), ReadWiiF32(memory, at(base, 4)),
                ReadWiiF32(memory, at(base, 8))};
    };
    const Vec3 local = WiiPrimitiveLocalPosition(memory, primitive);
    const Vec3 prepared = WiiPrimitivePreparedWorldPosition(memory, primitive);
    const Vec3 t = vec(at(state, 0x10));
    const Vec3 r0 = vec(at(state, 0x70));
    const Vec3 r1 = vec(at(state, 0x80));
    const Vec3 r2 = vec(at(state, 0x90));

    // PPC: y*row1; fmadds(x,row0); fmadds(z,row2); frsp;
    // fadds(state translation). Float/FMA host results are not FPSCR exact.
    const Vec3 transformed{
        std::fma(local.z, r2.x, std::fma(local.x, r0.x, local.y * r1.x)),
        std::fma(local.z, r2.y, std::fma(local.x, r0.y, local.y * r1.y)),
        std::fma(local.z, r2.z, std::fma(local.x, r0.z, local.y * r1.z))
    };
    const Vec3 world{transformed.x + t.x, transformed.y + t.y,
                     transformed.z + t.z};
    const Vec3 delta{world.x - prepared.x, world.y - prepared.y,
                     world.z - prepared.z};
    const Vec3 parameters = vec(at(primitive, 0x18));
    const auto shape = memory.ReadU32BE(at(primitive, 0x24));
    const bool identity = shape == 2u;
    WiiMatrix4 orientation{};
    if (identity) {
        // Original uses the constant identity matrix at 0x80569AD0.
        orientation = {1.f, 0.f, 0.f, 0.f,
                       0.f, 1.f, 0.f, 0.f,
                       0.f, 0.f, 1.f, 0.f,
                       0.f, 0.f, 0.f, 1.f};
    } else {
        // Source PPC computes state quaternion * primitive quaternion,
        // then invokes the already reconstructed VU0_quattom4.
        const WiiQuaternion s{
            ReadWiiF32(memory, state), ReadWiiF32(memory, at(state, 4)),
            ReadWiiF32(memory, at(state, 8)), ReadWiiF32(memory, at(state, 12))};
        const auto qbase = at(primitive, 8);
        const WiiQuaternion p{
            ReadWiiF32(memory, qbase), ReadWiiF32(memory, at(qbase, 4)),
            ReadWiiF32(memory, at(qbase, 8)), ReadWiiF32(memory, at(qbase, 12))};
        const WiiQuaternion composed{
            std::fma(s.x, p.w, std::fma(s.w, p.x,
                     std::fma(s.y, p.z, -s.z * p.y))),
            std::fma(s.y, p.w, std::fma(s.w, p.y,
                     std::fma(s.z, p.x, -s.x * p.z))),
            std::fma(s.z, p.w, std::fma(s.w, p.z,
                     std::fma(s.x, p.y, -s.y * p.x))),
            std::fma(-s.z, p.z, std::fma(-s.y, p.y,
                     std::fma(-s.x, p.x, s.w * p.w)))
        };
        orientation = WiiQuaternionToMatrix4(composed);
    }
    return {orientation, world, parameters, delta, shape, identity};
}

} // namespace undercover::vehicle
