#include "wii_rigidbody_detach.hpp"

#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::vehicle {
namespace {

std::uint32_t Offset(std::uint32_t address, std::uint32_t offset) {
    if (!address || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii Detach address");
    return address + offset;
}

void Require(bool available, const char* name) {
    if (!available) throw std::invalid_argument(name);
}

} // namespace

WiiDetachResult WiiRigidBodyBaseDetach(
    WiiMutableSnapshot& snapshot, std::uint32_t body,
    const WiiDetachCallbacks& callbacks) {
    // Original Detach__9RigidBodyFv at 0x8030E46C (160 bytes).
    WiiMutableSnapshot next = snapshot;
    const auto initial = next.ReadOnly();
    const auto state = RigidBodyStateAddress(initial, body);
    const auto flags = RigidBodyFlags(initial, body);
    if ((flags & 0x0002u) == 0)
        return {false, false, 0, 0};

    // Wii at 0x8030E490..0x8030E498: rlwinm clears ONLY 0x0002,
    // followed by sth state+0x1C.
    next.WriteU16BE(Offset(state, 0x1C),
                    static_cast<std::uint16_t>(flags & ~0x0002u));

    // Original body vtable slot +0x2E4 resolves to the base GetOwner
    // at 0x802F7A68. That base method reads body+0x2C directly.
    // Do not imply that derived classes necessarily use this method.
    const auto owner = next.ReadOnly().ReadU32BE(Offset(body, 0x2C));
    // The original immediately dereferences the returned owner pointer
    // (no null check). Host adapter rejects it with an exception.
    Require(owner != 0, "Wii Detach owner is null");
    Require(static_cast<bool>(callbacks.resolve_linked_object),
            "missing Wii owner virtual +0x7C callback");
    const auto linked = callbacks.resolve_linked_object(next, owner);
    if (!linked) {
        snapshot = std::move(next);
        return {true, false, owner, 0};
    }

    // 0x8030E4C8..0x8030E4D0 constructs a 32-bit local event constant.
    // PowerPC lis 0xC91C + signed addi 0x90D9 => 0xC91B90D9.
    constexpr std::uint32_t event = 0xC91B90D9u;
    Require(static_cast<bool>(callbacks.sim_get_time),
            "missing Wii Sim::GetTime host callback");
    Require(static_cast<bool>(callbacks.dispatch_linked_event),
            "missing Wii linked-object virtual +0x3C callback");
    // At 0x8030E4D4 original invokes Sim::GetTime and then invokes
    // virtual +0x3C on linked with pointer-to-constant, 0, 2.
    callbacks.sim_get_time(next);
    callbacks.dispatch_linked_event(next, linked, event, 0, 2);
    snapshot = std::move(next);
    return {true, true, owner, linked};
}

} // namespace undercover::vehicle
