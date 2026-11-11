#pragma once
#include <cstdint>
#include "wii_rigidbody_controls.hpp"
namespace undercover::vehicle {
// Wii DoDrag 0x8030ED34: branch gates only, not force equations.
// Flags are the unsigned halfword at RigidBody state +0x1C.
struct DragGateSelection { bool first; bool second; };
constexpr DragGateSelection SelectDoDragPaths(std::uint16_t flags) noexcept {
    return {(flags & 0x0002u) == 0 && (flags & 0x0800u) != 0,
            (flags & 0x0002u) == 0 && (flags & 0x0020u) != 0};
// Read the recovered unsigned state halfword through the verified Wii
// body -> wrapper -> state chain. No game process or binary is modified.
inline DragGateSelection SelectDoDragPathsFromSnapshot(
    const attrib::WiiAddressSpace& memory, std::uint32_t body) {
    return SelectDoDragPaths(RigidBodyFlags(memory, body));
}
}
}
