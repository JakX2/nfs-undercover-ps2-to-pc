#include "wii_rigidbody_transform.hpp"

#include <cmath>

namespace undercover::vehicle {

Vec3 WiiRigidBodyBaseConvertLocalToWorld(
    const attrib::WiiAddressSpace& m, std::uint32_t body,
    Vec3 local, bool include_translation) {
    // 0x8030F1B4..0x8030F274: source-backed loads and stores.
    // state+0x70 is original 4x4 orientation matrix, stored row-major;
    // the original method uses its first three COLUMNS, with input Y
    // as the initial multiply, then FMA X and FMA Z.
    const WiiMatrix4 matrix = RigidBodyOrientationMatrix(m, body);
    Vec3 world {
        std::fma(local.z, matrix[8],
                 std::fma(local.x, matrix[0], local.y * matrix[4])),
        std::fma(local.z, matrix[9],
                 std::fma(local.x, matrix[1], local.y * matrix[5])),
        std::fma(local.z, matrix[10],
                 std::fma(local.x, matrix[2], local.y * matrix[6]))
    };
    if (include_translation) {
        const Vec3 position = RigidBodyPosition(m, body);
        world.x += position.x;
        world.y += position.y;
        world.z += position.z;
    }
    return world;
}

} // namespace undercover::vehicle
