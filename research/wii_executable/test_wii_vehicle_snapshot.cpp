#include "wii_vehicle_snapshot.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;
using undercover::attrib::WiiAddressSpace;

static void Write32(std::vector<std::uint8_t>& bytes, std::size_t off, std::uint32_t v) {
    assert(off+4 <= bytes.size());
    bytes[off] = std::uint8_t(v >> 24);
    bytes[off+1] = std::uint8_t(v >> 16);
    bytes[off+2] = std::uint8_t(v >> 8);
    bytes[off+3] = std::uint8_t(v);
}
static void WriteF32(std::vector<std::uint8_t>& bytes, std::size_t off, float v) {
    std::uint32_t bits = 0;
    static_assert(sizeof(float) == 4, "float32 required");
    std::memcpy(&bits, &v, 4);
    Write32(bytes, off, bits);
}
static WiiAddressSpace Snapshot(float x, float y, float z) {
    constexpr std::uint32_t base = 0x80060000u;
    std::vector<std::uint8_t> bytes(0x800, 0);
    // rigid body at +0, wrapper +0x200, state +0x400, vehicle +0x600
    Write32(bytes, 0x70, base + 0x200);
    Write32(bytes, 0x200, base + 0x400);
    WriteF32(bytes, 0x400 + 0x20, x);
    WriteF32(bytes, 0x400 + 0x24, y);
    WriteF32(bytes, 0x400 + 0x28, z);
    WriteF32(bytes, 0x400 + 0x3C, 0.0005f);
    WriteF32(bytes, 0x400 + 0x6C, 1.25f);
    bytes[0x400 + 0x5E] = 0xA5;
    Write32(bytes, 0xFC, 0x11223344);
    WriteF32(bytes, 0x600 + 0x120, 13.25f);
    return WiiAddressSpace({{base, std::move(bytes)}});
}

template <class Err, class Fn> static void Throws(Fn f) {
    bool caught = false;
    try { f(); } catch (const Err&) { caught = true; }
    assert(caught);
}

int main() {
    constexpr std::uint32_t body = 0x80060000u;
    constexpr std::uint32_t vehicle = body + 0x600;
    const auto m = Snapshot(3.f, 4.f, 12.f);
    assert(RigidBodyStateAddress(m, body) == body + 0x400);
    const auto v = RigidBodyVelocity(m, body);
    assert(v.x == 3.f && v.y == 4.f && v.z == 12.f);
    assert(std::abs(RigidBodySpeed(m, body) - 13.f) < 0.0001f);
    assert(std::abs(RigidBodySpeedXZ(m, body) - std::sqrt(153.f)) < 0.0001f);
    assert(RigidBodyInverseMass(m, body) == 0.0005f);
    assert(RigidBodyRadius(m, body) == 1.25f);
    assert(RigidBodyIndex(m, body) == 0xA5);
    assert(RigidBodySimableType(m, body) == 0x11223344);
    assert(PVehicleSpeed(m, vehicle) == 13.25f);
    assert(!SimableSpeedKmh(false, true, 99.f));
    assert(!SimableSpeedKmh(true, false, 99.f));
    assert(std::abs(SimableSpeedKmh(true, true, 10.f) - 36.f) < 0.0001f);
    assert(SimableSpeedKmh(true, true, 0.f) == 0.f);
    assert(std::abs(SimableSpeedKmh(true, true, 100.f) - 360.f) < 0.001f);

    const auto zero = Snapshot(0.f, 0.f, 0.f);
    assert(RigidBodySpeed(zero, body) == 0.f);
    assert(RigidBodySpeedXZ(zero, body) == 0.f);
    const auto tiny = Snapshot(0.000001f, 0.f, 0.f);
    assert(RigidBodySpeed(tiny, body) == 0.f);  // Wii sqrt threshold
    const auto nan = Snapshot(std::numeric_limits<float>::quiet_NaN(), 0.f, 0.f);
    assert(RigidBodySpeed(nan, body) == 0.f);  // PPC's rsqrt unordered path
    Throws<std::out_of_range>([&] { (void)RigidBodyVelocity(m, 0); });
    Throws<std::out_of_range>([&] { (void)RigidBodyVelocity(m, body + 1); });
    Throws<std::out_of_range>([&] { (void)PVehicleSpeed(m, 0xFFFFFF00); });
    std::vector<std::uint8_t> broken(0x100, 0);
    Write32(broken, 0x70, 0xDEADBEE0);
    WiiAddressSpace unmapped({{body, std::move(broken)}});
    Throws<std::out_of_range>([&] { (void)RigidBodyStateAddress(unmapped, body); });
}
