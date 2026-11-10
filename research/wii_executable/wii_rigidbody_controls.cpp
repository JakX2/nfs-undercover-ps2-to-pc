#include "wii_rigidbody_controls.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {
std::uint32_t Add(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii RigidBody address");
    return address + offset;
}

std::uint16_t ReadU16BE(const attrib::WiiAddressSpace& m, std::uint32_t address) {
    if (address & 1) throw std::out_of_range("unaligned Wii halfword");
    const std::uint32_t second = Add(address, 1);
    return static_cast<std::uint16_t>(
        (std::uint16_t(m.ReadU8(address)) << 8) | m.ReadU8(second));
}

std::uint32_t StateField(const attrib::WiiAddressSpace& m, std::uint32_t body,
                         std::uint32_t offset) {
    return Add(RigidBodyStateAddress(m, body), offset);
}

Vec3 ReadVec3(const attrib::WiiAddressSpace& m, std::uint32_t base) {
    return {ReadWiiF32(m, base), ReadWiiF32(m, Add(base, 4)),
            ReadWiiF32(m, Add(base, 8))};
}

void PutFloatBE(std::uint8_t* out, float value) {
    static_assert(sizeof(float) == 4, "IEEE-754 float32 required");
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    out[0] = static_cast<std::uint8_t>(bits >> 24);
    out[1] = static_cast<std::uint8_t>(bits >> 16);
    out[2] = static_cast<std::uint8_t>(bits >> 8);
    out[3] = static_cast<std::uint8_t>(bits);
}
}  // namespace

std::uint16_t RigidBodyFlags(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // Get flags from state +0x1C (original uses lhz).
    return ReadU16BE(m, StateField(m, body, 0x1C));
}

bool RigidBodyIsAnchored(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // IsAnchored__9RigidBodyCFv, Wii 0x80301088; mask 0x0080.
    return (RigidBodyFlags(m, body) & 0x0080u) != 0;
}

bool RigidBodyHadPassiveCollision(const attrib::WiiAddressSpace& m,
                                   std::uint32_t body) {
    // HasHadPassiveCollision at 0x803010B0; rlwinm by 20 extracts bit 12.
    return (RigidBodyFlags(m, body) & 0x1000u) != 0;
}

bool RigidBodyHadWorldCollision(const attrib::WiiAddressSpace& m,
                                 std::uint32_t body) {
    // HasHadWorldCollision at 0x803010C4; extracts bit 2.
    return (RigidBodyFlags(m, body) & 0x0004u) != 0;
}

bool RigidBodyHadCollision(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // HasHadCollision at 0x803010D8; mask 0x000C, test nonzero.
    return (RigidBodyFlags(m, body) & 0x000Cu) != 0;
}

int RigidBodyContactCount(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetNumContactPoints at 0x8030100C: lbz + extsb, signed 8-bit.
    const int byte = m.ReadU8(StateField(m, body, 0x5C));
    return byte <= 127 ? byte : byte - 256;
}

bool RigidBodyIsInGroundContact(const attrib::WiiAddressSpace& m,
                                 std::uint32_t body) {
    // IsInGroundContact at 0x80301020: extsb then nonzero test.
    return RigidBodyContactCount(m, body) != 0;
}

bool RigidBodyIsSleeping(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // IsSleeping at 0x80301114; state +0x5D must equal 1.
    return m.ReadU8(StateField(m, body, 0x5D)) == 1;
}

bool RigidBodyIsModeling(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // IsModeling at 0x80301134 returns (state byte at +0x5D) != 2.
    // The name is counterintuitive. This follows the PPC arithmetic exactly.
    return m.ReadU8(StateField(m, body, 0x5D)) != 2;
}

float RigidBodyMass(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetMass__9RigidBodyCFv at 0x8030117C, state +0x2C.
    return ReadWiiF32(m, StateField(m, body, 0x2C));
}

float RigidBodyGravity(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetGravity__9RigidBodyCFv at 0x80300F90:
    // body +0x78 -> object +0xF0 float.
    const auto object = m.ReadU32BE(Add(body, 0x78));
    return ReadWiiF32(m, Add(object, 0xF0));
}

Vec3 RigidBodyForce(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetForce__9RigidBodyCFv at 0x80300FAC returns state+0x50.
    return ReadVec3(m, StateField(m, body, 0x50));
}

Vec3 RigidBodyTorque(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetTorque__9RigidBodyCFv at 0x80300F9C returns state+0x60.
    return ReadVec3(m, StateField(m, body, 0x60));
}

Vec3 RigidBodyCenterOfGravity(const attrib::WiiAddressSpace& m,
                               std::uint32_t body) {
    // GetCenterOfGravity__9RigidBodyCFv at 0x80301174 returns body +0xE4.
    return ReadVec3(m, Add(body, 0xE4));
}

WiiMutableSnapshot::WiiMutableSnapshot(std::vector<attrib::WiiMemoryRegion> regions)
    : regions_(std::move(regions)) {
    // Delegate input limits, overlaps and wraparound to the existing,
    // independently tested read-only Wii address-space validator.
    (void)attrib::WiiAddressSpace(regions_);
}

attrib::WiiAddressSpace WiiMutableSnapshot::ReadOnly() const {
    return attrib::WiiAddressSpace(regions_);
}

void WiiMutableSnapshot::WriteBytes(std::uint32_t address,
                                    const std::uint8_t* bytes, std::size_t length) {
    if (!address || !bytes || !length ||
        std::uint64_t(address) + length > (std::uint64_t(1) << 32))
        throw std::out_of_range("invalid Wii write span");
    for (auto& region : regions_) {
        if (address < region.base) continue;
        const std::uint64_t relative = std::uint64_t(address) - region.base;
        if (relative > region.bytes.size() ||
            length > region.bytes.size() - relative)
            continue;
        std::copy_n(bytes, length, region.bytes.begin() +
                                      static_cast<std::size_t>(relative));
        return;
    }
    // All bounds are verified before writing any byte. No partial mutation.
    throw std::out_of_range("unmapped or split Wii write span");
}

void WiiMutableSnapshot::WriteU16BE(std::uint32_t address, std::uint16_t value) {
    if (address & 1) throw std::out_of_range("unaligned Wii halfword write");
    const std::array<std::uint8_t, 2> bytes{
        static_cast<std::uint8_t>(value >> 8),
        static_cast<std::uint8_t>(value)
    };
    WriteBytes(address, bytes.data(), bytes.size());
}

void WiiMutableSnapshot::WriteVec3BE(std::uint32_t address, Vec3 value) {
    if (address & 3) throw std::out_of_range("unaligned Wii float vector write");
    std::array<std::uint8_t, 12> bytes{};
    PutFloatBE(bytes.data(), value.x);
    PutFloatBE(bytes.data() + 4, value.y);
    PutFloatBE(bytes.data() + 8, value.z);
    WriteBytes(address, bytes.data(), bytes.size());
}

void RigidBodySetAnchored(WiiMutableSnapshot& m, std::uint32_t body, bool anchored) {
    // SetAnchored__9RigidBodyFb at 0x80301050: OR/clear 0x0080.
    const auto snapshot = m.ReadOnly();
    const auto address = StateField(snapshot, body, 0x1C);
    const auto old = ReadU16BE(snapshot, address);
    m.WriteU16BE(address, anchored ? std::uint16_t(old | 0x0080u)
                                  : std::uint16_t(old & ~0x0080u));
}

void RigidBodySetForce(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value) {
    // SetForce__9RigidBodyFRCQ25UMath7Vector3 at 0x80300FE0.
    m.WriteVec3BE(StateField(m.ReadOnly(), body, 0x50), value);
}

void RigidBodySetTorque(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value) {
    // SetTorque__9RigidBodyFRCQ25UMath7Vector3 at 0x80300FBC.
    m.WriteVec3BE(StateField(m.ReadOnly(), body, 0x60), value);
}

void RigidBodySetCenterOfGravity(WiiMutableSnapshot& m, std::uint32_t body,
                                  Vec3 value) {
    // SetCenterOfGravity__9RigidBodyFRCQ25UMath7Vector3 at 0x803010F8:
    // writes body+0xE4/+0xE8/+0xEC, not state.
    const auto address = Add(body, 0xE4);
    (void)m.ReadOnly().ReadU32BE(address); // validate owner-local body range.
    m.WriteVec3BE(address, value);
}

}  // namespace undercover::vehicle
