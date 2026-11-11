#pragma once

#include <cstdint>

#include "wii_rigidbody_controls.hpp"

namespace undercover::vehicle {

// Wii DoDrag at 0x8030ED34: branch gates only, not drag-force equations.
// Flags are the unsigned big-endian halfword at RigidBody state +0x1C.
struct DragGateSelection {
    bool first;
    bool second;
};

constexpr DragGateSelection SelectDoDragPaths(std::uint16_t flags) noexcept {
    const bool allowed = (flags & 0x0002u) == 0;
    return {allowed && (flags & 0x0800u) != 0,
            allowed && (flags & 0x0020u) != 0};
}

// Read the recovered state halfword through the verified Wii
// body -> wrapper -> state chain. No original game data is modified.
inline DragGateSelection SelectDoDragPathsFromSnapshot(
    const attrib::WiiAddressSpace& memory, std::uint32_t body) {
    return SelectDoDragPaths(RigidBodyFlags(memory, body));
}

} // namespace undercover::vehicle
