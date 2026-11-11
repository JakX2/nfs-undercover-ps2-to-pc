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

} // namespace undercover::vehicle
