#pragma once

#include "wii_vehicle_snapshot.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace undercover::vehicle {

// Source-backed Wii RigidBody field accessors. All 32-bit addresses are
// EMULATED Wii addresses, never native pointers.
std::uint16_t RigidBodyFlags(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyIsAnchored(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyHadPassiveCollision(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyHadWorldCollision(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyHadCollision(const attrib::WiiAddressSpace& m, std::uint32_t body);
int RigidBodyContactCount(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyIsInGroundContact(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyIsSleeping(const attrib::WiiAddressSpace& m, std::uint32_t body);
bool RigidBodyIsModeling(const attrib::WiiAddressSpace& m, std::uint32_t body);
float RigidBodyMass(const attrib::WiiAddressSpace& m, std::uint32_t body);
float RigidBodyGravity(const attrib::WiiAddressSpace& m, std::uint32_t body);
Vec3 RigidBodyPosition(const attrib::WiiAddressSpace& m, std::uint32_t body);
Vec3 RigidBodyAngularVelocity(const attrib::WiiAddressSpace& m, std::uint32_t body);
Vec3 RigidBodyForce(const attrib::WiiAddressSpace& m, std::uint32_t body);
Vec3 RigidBodyTorque(const attrib::WiiAddressSpace& m, std::uint32_t body);
Vec3 RigidBodyCenterOfGravity(const attrib::WiiAddressSpace& m, std::uint32_t body);

// Writable *private synthetic snapshot*, not a retail Wii memory editor.
// A mutation changes only this host-owned byte vector; no process attach,
// emulator hook or original game-file writes occur.
class WiiMutableSnapshot {
public:
    explicit WiiMutableSnapshot(std::vector<attrib::WiiMemoryRegion> regions);
    attrib::WiiAddressSpace ReadOnly() const;
    void WriteU16BE(std::uint32_t address, std::uint16_t value);
    void WriteVec3BE(std::uint32_t address, Vec3 value);

private:
    void WriteBytes(std::uint32_t address, const std::uint8_t* bytes,
                    std::size_t length);
    std::vector<attrib::WiiMemoryRegion> regions_;
};

void RigidBodySetAnchored(WiiMutableSnapshot& m, std::uint32_t body, bool anchored);
void RigidBodySetPosition(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);
void RigidBodySetLinearVelocity(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);
void RigidBodySetAngularVelocity(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);
void RigidBodySetForce(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);
void RigidBodySetTorque(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);
void RigidBodySetCenterOfGravity(WiiMutableSnapshot& m, std::uint32_t body, Vec3 value);

 // Partial, isolated reconstruction of the FIRST state writes in Wii
 // DoIntegration__9RigidBodyFf (0x8030F9C4). This DOES NOT simulate a frame:
 // it stops after the three state velocity stores or the inactive zeroing.
 enum class IntegrationPrefixPath { inactive_cleared, active_velocity_updated };
 IntegrationPrefixPath ApplyDoIntegrationVelocityPrefix(
     WiiMutableSnapshot& m, std::uint32_t body, float timestep);

// V8 extends the verified active path only as far as 0x8030FB2C:
// linear velocity FMA, torque *= timestep, position += velocity*timestep.
// Neither angular integration nor later clamps are included. The previous
// V7 prefix remains available for an isolated comparison.
IntegrationPrefixPath ApplyDoIntegrationTranslationPrefix(
    WiiMutableSnapshot& m, std::uint32_t body, float timestep);

}  // namespace undercover::vehicle
