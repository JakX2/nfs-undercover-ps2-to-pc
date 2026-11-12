#include "wii_rigidbody_transform.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>

namespace undercover::vehicle {
namespace {
std::uint32_t Add(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii transform state address");
    return address + offset;
}
} // namespace

Vec3 WiiRigidBodyBaseConvertLocalToWorld(
    const attrib::WiiAddressSpace& m, std::uint32_t body,
    Vec3 local, bool include_translation) {
    // 0x8030F1B4..0x8030F274: original source-backed loads/stores.
    // state+0x70 holds the original 4x4 orientation matrix. Only
    // NINE entries of its upper-left 3x3 are read by the Wii method.
    // Each output begins with input.y*matrix-row1, then FMA input.x
    // against row0, then FMA input.z against row2.
    const auto state = RigidBodyStateAddress(m, body);
    const auto at = [&](std::uint32_t offset) {
        return ReadWiiF32(m, Add(state, offset));
    };
    const Vec3 world {
        std::fma(local.z, at(0x90),
                 std::fma(local.x, at(0x70), local.y * at(0x80))),
        std::fma(local.z, at(0x94),
                 std::fma(local.x, at(0x74), local.y * at(0x84))),
        std::fma(local.z, at(0x98),
                 std::fma(local.x, at(0x78), local.y * at(0x88)))
    };
    if (!include_translation) return world;
    const Vec3 position = {
        at(0x10), at(0x14), at(0x18)
    };
    return {world.x + position.x,
            world.y + position.y,
            world.z + position.z};
}

Vec3 WiiRigidBodyBaseConvertWorldToLocal(
    const attrib::WiiAddressSpace& m, std::uint32_t body,
    Vec3 world, bool include_translation) {
    // Wii 0x8030F27C..0x8030F418. The original subtracts position
    // before transposing the matrix whenever its boolean is nonzero.
    const auto state = RigidBodyStateAddress(m, body);
    const auto at = [&](std::uint32_t offset) {
        return ReadWiiF32(m, Add(state, offset));
    };
    if (include_translation) {
        world.x -= at(0x10);
        world.y -= at(0x14);
        world.z -= at(0x18);
    }

    // The original unconditionally reads and transposes the *full*
    // 4x4 matrix to stack space. Read all 16 words even though only
    // 9 of them participate in the final vector multiplication.
    // This matters for rejecting incomplete Wii source snapshots.
    WiiMatrix4 rotation{};
    for (std::size_t i = 0; i < rotation.size(); ++i)
        rotation[i] = at(0x70u + std::uint32_t(i) * 4u);

    // In the original PPC temp matrix, each output starts with
    // world.y times transposed row1, then FMA world.x and world.z.
    // Expressed directly using the ORIGINAL (untransposed) matrix:
    return {
        std::fma(world.z, rotation[2],
                 std::fma(world.x, rotation[0], world.y * rotation[1])),
        std::fma(world.z, rotation[6],
                 std::fma(world.x, rotation[4], world.y * rotation[5])),
        std::fma(world.z, rotation[10],
                 std::fma(world.x, rotation[8], world.y * rotation[9]))
    };
}

} // namespace undercover::vehicle
