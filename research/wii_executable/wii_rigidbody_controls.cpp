#include "wii_rigidbody_controls.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <cmath>
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

Vec3 RigidBodyPosition(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetPosition__9RigidBodyCFv at 0x803012B8, returns state +0x10.
    return ReadVec3(m, StateField(m, body, 0x10));
}

Vec3 RigidBodyAngularVelocity(const attrib::WiiAddressSpace& m, std::uint32_t body) {
    // GetAngularVelocity__9RigidBodyCFv at 0x803012A8, state+0x30.
    return ReadVec3(m, StateField(m, body, 0x30));
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

void RigidBodySetPosition(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value) {
    // SetPosition__9RigidBodyFRCQ25UMath7Vector3 at 0x8030E3B4.
    m.WriteVec3BE(StateField(m.ReadOnly(), body, 0x10), value);
}

void RigidBodySetLinearVelocity(WiiMutableSnapshot& m, std::uint32_t body,
                                Vec3 value) {
    // SetLinearVelocity__9RigidBodyFRCQ25UMath7Vector3 at 0x8030E3D8.
    m.WriteVec3BE(StateField(m.ReadOnly(), body, 0x20), value);
}

void RigidBodySetAngularVelocity(WiiMutableSnapshot& m, std::uint32_t body,
                                 Vec3 value) {
    // SetAngularVelocity__9RigidBodyFRCQ25UMath7Vector3 at 0x8030E3FC.
    m.WriteVec3BE(StateField(m.ReadOnly(), body, 0x30), value);
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

// Only the first velocity-state operation of the 0x8030F9C4 Wii integrator.
// Original PPC at 0x8030F9FC..0x8030FA24: if state+0x5D != 0, zero
// the six float32 slots at state+0x20..+0x28 and +0x30..+0x38
// and branch to the final epilogue. No force or position update.
// Otherwise, 0x8030FA28..0x8030FAD8 applies
// velocity += force * (timestep * inverse_mass) via fmadds.
// Other torque/orientation/position updates later in the original routine
// are intentionally outside this prefix.
IntegrationPrefixPath ApplyDoIntegrationVelocityPrefix(
    WiiMutableSnapshot& m, std::uint32_t body, float timestep) {
    const auto before = m.ReadOnly();
    const auto state = RigidBodyStateAddress(before, body);
    const std::uint32_t velocity_at = Add(state, 0x20);
    const std::uint32_t second_at = Add(state, 0x30);
    const auto status = before.ReadU8(Add(state, 0x5D));
    // Copy-on-commit: malformed or split state mappings never leave
    // the caller's synthetic bytes half-mutated.
    WiiMutableSnapshot next = m;
    if (status != 0) {
        next.WriteVec3BE(velocity_at, {0.f, 0.f, 0.f});
        next.WriteVec3BE(second_at, {0.f, 0.f, 0.f});
        m = std::move(next);
        return IntegrationPrefixPath::inactive_cleared;
    }
    const float inverse_mass = ReadWiiF32(before, Add(state, 0x3C));
    const float factor = timestep * inverse_mass; // fmuls f29,f1,f0
    const auto force = ReadVec3(before, Add(state, 0x50));
    const auto velocity = ReadVec3(before, velocity_at);
    const Vec3 updated = {
        std::fma(force.x, factor, velocity.x),
        std::fma(force.y, factor, velocity.y),
        std::fma(force.z, factor, velocity.z)
    };
    next.WriteVec3BE(velocity_at, updated);
    m = std::move(next);
    return IntegrationPrefixPath::active_velocity_updated;
}

// V8 extends the verified original 0x8030FA28..0x8030FB2C active path.
// After force-to-linear-velocity FMA, the Wii code scales the stored torque
// vector at state+0x60 by dt, then advances position at state+0x10 using
// the just-updated velocity. It also computes angular-inertia intermediates
// which are intentionally NOT reconstructed here. This function is NOT a
// complete DoIntegration update, nor a live Wii memory patcher.
IntegrationPrefixPath ApplyDoIntegrationTranslationPrefix(
    WiiMutableSnapshot& m, std::uint32_t body, float timestep) {
    // One outer transaction includes all three disjoint affected areas.
    // Even if position or torque validation fails after updating velocity in
    // the private next snapshot, the caller's original bytes are unchanged.
    WiiMutableSnapshot next = m;
    const IntegrationPrefixPath path =
        ApplyDoIntegrationVelocityPrefix(next, body, timestep);
    if (path == IntegrationPrefixPath::inactive_cleared) {
        m = std::move(next);
        return path;
    }
    const auto snapshot = next.ReadOnly();
    const std::uint32_t state = RigidBodyStateAddress(snapshot, body);
    const Vec3 torque = ReadVec3(snapshot, Add(state, 0x60));
    const Vec3 position = ReadVec3(snapshot, Add(state, 0x10));
    const Vec3 velocity = ReadVec3(snapshot, Add(state, 0x20));
    const Vec3 scaled_torque{
        torque.x * timestep,
        torque.y * timestep,
        torque.z * timestep
    };
    const Vec3 updated_position{
        std::fma(velocity.x, timestep, position.x),
        std::fma(velocity.y, timestep, position.y),
        std::fma(velocity.z, timestep, position.z)
    };
    next.WriteVec3BE(Add(state, 0x60), scaled_torque);
    next.WriteVec3BE(Add(state, 0x10), updated_position);
    m = std::move(next);
    return IntegrationPrefixPath::active_velocity_updated;
}

// Original Wii DoIntegration branch at 0x8030FB2C..0x8030FBD8.
// The body-side 3x3 matrix multiplies the timestep-scaled torque.
// The three components overwrite the torque workspace, then accumulate into
// the existing state+0x30 angular velocity. PPC uses fmuls/fmadds here;
// host std::fma tracks the operation order but not Wii FP rounding modes.
// The later angular clamps/orientation stores remain OUTSIDE this function.
IntegrationPrefixPath ApplyDoIntegrationAngularPrefix(
    WiiMutableSnapshot& m, std::uint32_t body, float timestep) {
    WiiMutableSnapshot next = m;
    const IntegrationPrefixPath path =
        ApplyDoIntegrationTranslationPrefix(next, body, timestep);
    if (path == IntegrationPrefixPath::inactive_cleared) {
        m = std::move(next);
        return path;
    }
    const auto r = next.ReadOnly();
    const std::uint32_t state = RigidBodyStateAddress(r, body);
    const Vec3 scaled = ReadVec3(r, Add(state, 0x60));
    const Vec3 angular = ReadVec3(r, Add(state, 0x30));

    const Vec3 first = ReadVec3(r, Add(body, 0x84));
    const Vec3 second = ReadVec3(r, Add(body, 0x94));
    const Vec3 third = ReadVec3(r, Add(body, 0xA4));

    // Original per-component summation:
    // delta.x = tz * Mzx + tx * Mxx + ty * Myx
    // delta.y = tz * Mzy + tx * Mxy + ty * Myy
    // delta.z = tz * Mzz + tx * Mxz + ty * Myz
    // The order of the inner FMA terms follows the PPC instruction sequence.
    const Vec3 delta {
        std::fma(scaled.z, third.x,
                 std::fma(scaled.x, first.x, scaled.y * second.x)),
        std::fma(scaled.z, third.y,
                 std::fma(scaled.x, first.y, scaled.y * second.y)),
        std::fma(scaled.z, third.z,
                 std::fma(scaled.x, first.z, scaled.y * second.z))
    };
    const Vec3 new_angular {
        angular.x + delta.x,
        angular.y + delta.y,
        angular.z + delta.z
    };
    next.WriteVec3BE(Add(state, 0x60), delta);
    next.WriteVec3BE(Add(state, 0x30), new_angular);
    m = std::move(next);
    return IntegrationPrefixPath::active_velocity_updated;
}


// V10 continues from 0x8030FBD8 to the last clamp store 0x8030FCF0.
// Original constants from the owner's Wii ELF .sdata2 are:
//   r2-24500 -> +300.0f, r2-24496 -> -300.0f
//   r2-24492 ->  +30.0f, r2-24488 ->  -30.0f.
// PPC comparisons use ordered floating point. The first comparison against
// the upper bound is LT; unordered comparisons take the upper branch.
// The second comparison checks whether the lower bound is GREATER than
// the upper-capped value. Host comparison ordering deliberately mirrors it.
namespace {
float ClampWiiComponent(float value, float lower, float upper) {
    const float upper_capped = (value < upper) ? value : upper;
    return (lower > upper_capped) ? lower : upper_capped;
}
Vec3 ClampWiiVec(Vec3 v, float bound) {
    return {ClampWiiComponent(v.x, -bound, bound),
            ClampWiiComponent(v.y, -bound, bound),
            ClampWiiComponent(v.z, -bound, bound)};
}
}  // namespace

IntegrationPrefixPath ApplyDoIntegrationClampedAngularPrefix(
    WiiMutableSnapshot& m, std::uint32_t body, float timestep) {
    WiiMutableSnapshot next = m;
    const auto path = ApplyDoIntegrationAngularPrefix(next, body, timestep);
    if (path == IntegrationPrefixPath::inactive_cleared) {
        m = std::move(next);
        return path;
    }
    const auto view = next.ReadOnly();
    const std::uint32_t state = RigidBodyStateAddress(view, body);
    const Vec3 linear = ReadVec3(view, Add(state, 0x20));
    const Vec3 angular = ReadVec3(view, Add(state, 0x30));
    next.WriteVec3BE(Add(state, 0x20), ClampWiiVec(linear, 300.f));
    next.WriteVec3BE(Add(state, 0x30), ClampWiiVec(angular, 30.f));
    m = std::move(next);
    return IntegrationPrefixPath::active_velocity_updated;
}

}  // namespace undercover::vehicle
