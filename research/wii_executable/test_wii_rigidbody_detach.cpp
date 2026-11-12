#include "wii_rigidbody_detach.hpp"
#include "wii_rigidbody_resolve.hpp"

#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t body = 0x80060000u;
constexpr std::uint32_t state = body + 0x400u;
constexpr std::uint32_t owner = body + 0x600u;
constexpr std::uint32_t linked = body + 0x700u;

void Put32(std::vector<std::uint8_t>& b, std::size_t off, std::uint32_t value) {
    assert(off + 4 <= b.size());
    b[off] = std::uint8_t(value >> 24);
    b[off + 1] = std::uint8_t(value >> 16);
    b[off + 2] = std::uint8_t(value >> 8);
    b[off + 3] = std::uint8_t(value);
}

WiiMutableSnapshot Fixture(std::uint16_t flags=0x0842u,
                           std::uint32_t owner_address=owner,
                           std::uint8_t status=1) {
    std::vector<std::uint8_t> bytes(0x900, 0);
    Put32(bytes, 0x70, body + 0x200);
    Put32(bytes, 0x200, state);
    Put32(bytes, 0x2C, owner_address);
    bytes[0x400 + 0x1C] = std::uint8_t(flags >> 8);
    bytes[0x400 + 0x1D] = std::uint8_t(flags);
    bytes[0x400 + 0x5D] = status;
    return WiiMutableSnapshot({{body, std::move(bytes)}});
}
template <class Error, class Fn> void ExpectThrow(Fn f) {
    bool caught = false;
    try { f(); } catch (const Error&) { caught = true; }
    assert(caught);
}

void TestNoAttachedFlagShortCircuits() {
    auto m = Fixture(0x0840);
    const auto result = WiiRigidBodyBaseDetach(m, body, {});
    assert(!result.cleared_attached_flag && !result.event_sent);
    assert(result.owner == 0 && result.linked_object == 0);
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0840);
}

void TestClearsFlagThenResolvesOwner() {
    auto m = Fixture();
    std::vector<std::string> order;
    WiiDetachCallbacks callbacks;
    callbacks.resolve_linked_object = [&](WiiMutableSnapshot& next,
                                          std::uint32_t got_owner) {
        assert(got_owner == owner);
        assert(RigidBodyFlags(next.ReadOnly(), body) == 0x0840u);
        order.emplace_back("resolve");
        return linked;
    };
    callbacks.sim_get_time = [&](WiiMutableSnapshot&) {
        order.emplace_back("time");
    };
    callbacks.dispatch_linked_event = [&](WiiMutableSnapshot& next,
                                          std::uint32_t target,
                                          std::uint32_t code,
                                          std::uint32_t arg5,
                                          std::uint32_t arg6) {
        assert(target == linked);
        assert(code == 0xC91B90D9u);
        assert(arg5 == 0 && arg6 == 2);
        assert(RigidBodyFlags(next.ReadOnly(), body) == 0x0840u);
        order.emplace_back("event");
        next.WriteU16BE(state + 0x1C, 0x0848u);
    };
    const auto result = WiiRigidBodyBaseDetach(m, body, callbacks);
    assert(result.cleared_attached_flag && result.event_sent);
    assert(result.owner == owner && result.linked_object == linked);
    assert((order == std::vector<std::string>{"resolve", "time", "event"}));
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0848u);
    assert(m.ReadOnly().ReadU8(state + 0x5D) == 1);
}

void TestNullLinkedObjectSkipsEvent() {
    auto m = Fixture();
    int resolves = 0;
    WiiDetachCallbacks callbacks;
    callbacks.resolve_linked_object = [&](WiiMutableSnapshot&, std::uint32_t) {
        ++resolves;
        return std::uint32_t(0);
    };
    const auto result = WiiRigidBodyBaseDetach(m, body, callbacks);
    assert(resolves == 1);
    assert(result.cleared_attached_flag && !result.event_sent);
    assert(result.owner == owner && result.linked_object == 0);
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0840u);
}

void TestResolveForceInvokesRealDetachBranch() {
    auto m = Fixture(0x0002u);
    int resolutions = 0;
    WiiDetachCallbacks callbacks;
    callbacks.resolve_linked_object = [&](WiiMutableSnapshot&, std::uint32_t) {
        ++resolutions;
        return std::uint32_t(0);
    };
    const auto original_detach = [&](WiiMutableSnapshot& next,
                                     std::uint32_t target) {
        const auto result = WiiRigidBodyBaseDetach(next, target, callbacks);
        assert(result.cleared_attached_flag);
    };
    const auto resolved =
        WiiRigidBodyBaseResolveForce(m, body, {1.f, 2.f, 3.f}, original_detach);
    assert(resolved == WiiResolveResult::accumulated);
    assert(resolutions == 1);
    // ResolveForce ORs 0x0040 first; Detach then clears 0x0002.
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0040u);
    assert(m.ReadOnly().ReadU8(state + 0x5D) == 0);
    const auto force = RigidBodyForce(m.ReadOnly(), body);
    assert(force.x == 1 && force.y == 2 && force.z == 3);
}

void TestMissingCallbacksAndNullOwnerRollback() {
    auto m = Fixture();
    ExpectThrow<std::invalid_argument>([&] {
        (void)WiiRigidBodyBaseDetach(m, body, {});
    });
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0842);
    auto null_owner = Fixture(0x0842, 0);
    ExpectThrow<std::invalid_argument>([&] {
        (void)WiiRigidBodyBaseDetach(null_owner, body, {});
    });
    assert(RigidBodyFlags(null_owner.ReadOnly(), body) == 0x0842);

    WiiDetachCallbacks callbacks;
    callbacks.resolve_linked_object = [](WiiMutableSnapshot& next, std::uint32_t) {
        next.WriteU16BE(state + 0x1C, 0xFFFF);
        return linked;
    };
    ExpectThrow<std::invalid_argument>([&] {
        (void)WiiRigidBodyBaseDetach(m, body, callbacks);
    });
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0842);

    callbacks.sim_get_time = [](WiiMutableSnapshot&) {};
    callbacks.dispatch_linked_event = [](WiiMutableSnapshot& next,
                                         std::uint32_t, std::uint32_t,
                                         std::uint32_t, std::uint32_t) {
        next.WriteU16BE(state + 0x1C, 0xFFFF);
        throw std::runtime_error("opaque linked event failed");
    };
    ExpectThrow<std::runtime_error>([&] {
        (void)WiiRigidBodyBaseDetach(m, body, callbacks);
    });
    assert(RigidBodyFlags(m.ReadOnly(), body) == 0x0842);
}
} // namespace

int main() {
    TestNoAttachedFlagShortCircuits();
    TestClearsFlagThenResolvesOwner();
    TestNullLinkedObjectSkipsEvent();
    TestResolveForceInvokesRealDetachBranch();
    TestMissingCallbacksAndNullOwnerRollback();
}
