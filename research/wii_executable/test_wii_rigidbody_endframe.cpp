#include "wii_rigidbody_endframe.hpp"

#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x400;
constexpr std::uint32_t kCollider = kBody + 0x700;
constexpr std::uint32_t kManager = kBody + 0x740;
constexpr std::uint32_t kWorldPosition = kBody + 0x780;

void Put32(std::vector<std::uint8_t>& bytes, std::size_t at,
           std::uint32_t value) {
    assert(at + 4 <= bytes.size());
    bytes[at] = static_cast<std::uint8_t>(value >> 24);
    bytes[at + 1] = static_cast<std::uint8_t>(value >> 16);
    bytes[at + 2] = static_cast<std::uint8_t>(value >> 8);
    bytes[at + 3] = static_cast<std::uint8_t>(value);
}

WiiMutableSnapshot Fixture(std::uint8_t status=0, std::uint16_t flags=0x040C,
                           std::uint32_t collider=kCollider,
                           std::uint32_t manager=kManager) {
    std::vector<std::uint8_t> bytes(0x800, 0);
    Put32(bytes, 0x70, kBody + 0x200); // wrapper
    Put32(bytes, 0x200, kState);
    Put32(bytes, 0xE0, collider);
    Put32(bytes, 0x2C, manager);
    bytes[0x400 + 0x1C] = static_cast<std::uint8_t>(flags >> 8);
    bytes[0x400 + 0x1D] = static_cast<std::uint8_t>(flags);
    bytes[0x400 + 0x5D] = status;
    return WiiMutableSnapshot({{kBody, std::move(bytes)}});
}

template<class Err, class F> void MustThrow(F action) {
    bool failed = false;
    try { action(); } catch (const Err&) { failed = true; }
    assert(failed);
}

void TestAllActiveCallbacksInSourceOrder() {
    auto state = Fixture();
    std::vector<std::string> order;
    WiiEndFrameCallbacks cb;
    cb.update_collider = [&](WiiMutableSnapshot& m, std::uint32_t body) {
        assert(body == kBody);
        order.emplace_back("collider");
        assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x040C);
        m.WriteU16BE(kState + 0x1C, 0x048C); // simulate source callback
    };
    cb.is_collider_empty = [&](const WiiMutableSnapshot& m, std::uint32_t object) {
        assert(object == kCollider);
        // Original clears 0x0004 between these two callbacks.
        assert(RigidBodyFlags(m.ReadOnly(), kBody) == 0x0488);
        order.emplace_back("empty");
        return false;
    };
    cb.world_collisions = [&](WiiMutableSnapshot& m, std::uint32_t body, float dt) {
        assert(body == kBody && dt == 0.5f); // original 2.0 multiplier
        order.emplace_back("world");
        auto flags = RigidBodyFlags(m.ReadOnly(), kBody);
        m.WriteU16BE(kState + 0x1C, std::uint16_t(flags | 0x1000u));
    };
    cb.do_drag = [&](WiiMutableSnapshot& m, std::uint32_t body) {
        assert(body == kBody);
        order.emplace_back("drag");
        RigidBodySetForce(m, body, {1.f, 2.f, 3.f});
    };
    cb.should_sleep = [&](WiiMutableSnapshot& m, std::uint32_t body) {
        assert(body == kBody);
        order.emplace_back("virtual");
        assert(RigidBodyForce(m.ReadOnly(), body).y == 2.f);
        return true;
    };
    const auto result = ApplyRigidBodyOnEndFrame(state, kBody, .25f, true, cb);
    assert((order == std::vector<std::string>{"collider", "empty", "world",
                                               "drag", "virtual"}));
    assert(result.collider_updated && result.world_collisions_dispatched);
    assert(result.drag_dispatched && result.entered_sleeping_state);
    assert(!result.world_position_synced);
    assert(result.entry_status == 0 && result.exit_status == 1);
    assert(result.exit_flags == 0x1088);
    assert(RigidBodyFlags(state.ReadOnly(), kBody) == 0x1088);
    assert(state.ReadOnly().ReadU8(kState + 0x5D) == 1);
}

void TestCollisionPassAndEmptyBranches() {
    for (bool enabled : {false, true}) {
        auto s = Fixture();
        std::vector<std::string> order;
        WiiEndFrameCallbacks cb;
        cb.update_collider = [&](WiiMutableSnapshot&, std::uint32_t) {
            order.emplace_back("update");
        };
        cb.is_collider_empty = [&](const WiiMutableSnapshot&, std::uint32_t) {
            order.emplace_back("empty");
            return true;
        };
        cb.do_drag = [&](WiiMutableSnapshot&, std::uint32_t) {
            order.emplace_back("drag");
        };
        cb.should_sleep = [&](WiiMutableSnapshot&, std::uint32_t) {
            order.emplace_back("virtual");
            return false;
        };
        auto r = ApplyRigidBodyOnEndFrame(s, kBody, 1.f, enabled, cb);
        assert(!r.world_collisions_dispatched);
        assert(!r.entered_sleeping_state && r.exit_status == 0);
        assert(r.collider_updated == enabled && r.drag_dispatched);
        assert(r.exit_flags == (enabled ? 0x0008 : 0x000C));
        if (enabled) {
            assert((order == std::vector<std::string>{"update", "empty",
                                                       "drag", "virtual"}));
        } else {
            assert((order == std::vector<std::string>{"drag", "virtual"}));
        }
    }
}

void TestInactiveWorldPositionSynchronization() {
    for (std::uint8_t status : {std::uint8_t(1), std::uint8_t(2),
                                std::uint8_t(255)}) {
        auto s = Fixture(status);
        std::vector<std::string> order;
        WiiEndFrameCallbacks cb;
        cb.resolve_world_position = [&](WiiMutableSnapshot&, std::uint32_t manager) {
            order.emplace_back("resolve");
            assert(manager == kManager);
            return kWorldPosition;
        };
        cb.sync_world_position = [&](WiiMutableSnapshot& m, std::uint32_t position,
                                     std::uint32_t source_position,
                                     std::uint32_t source_orientation) {
            order.emplace_back("sync");
            assert(position == kWorldPosition);
            assert(source_position == kState + 0x10);
            assert(source_orientation == kBody + 0xC4);
            RigidBodySetPosition(m, kBody, {4.f, 5.f, 6.f});
        };
        auto r = ApplyRigidBodyOnEndFrame(s, kBody, 4.f, true, cb);
        assert((order == std::vector<std::string>{"resolve", "sync"}));
        assert(!r.collider_updated && !r.world_collisions_dispatched);
        assert(!r.drag_dispatched && !r.entered_sleeping_state);
        assert(r.world_position_synced);
        assert(r.entry_status == status && r.exit_status == status);
        assert(r.exit_flags == 0x000C); // world collision flag NOT cleared
        assert(RigidBodyPosition(s.ReadOnly(), kBody).y == 5.f);
    }
}

void TestMissingCallbacksAreAtomic() {
    // Partially executed callbacks must not publish source-state changes.
    auto active = Fixture();
    WiiEndFrameCallbacks cb;
    cb.update_collider = [&](WiiMutableSnapshot& m, std::uint32_t) {
        m.WriteU16BE(kState + 0x1C, 0xFFFF);
    };
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnEndFrame(active, kBody, 2.f, true, cb);
    });
    assert(RigidBodyFlags(active.ReadOnly(), kBody) == 0x040C);
    assert(active.ReadOnly().ReadU8(kState + 0x5D) == 0);

    auto bad_collider = Fixture(0, 0x040C, 0);
    cb.is_collider_empty = [](const WiiMutableSnapshot&, std::uint32_t) {
        return true;
    };
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnEndFrame(bad_collider, kBody, 1.f, true, cb);
    });
    assert(RigidBodyFlags(bad_collider.ReadOnly(), kBody) == 0x040C);

    auto late_failure = Fixture();
    cb.do_drag = [&](WiiMutableSnapshot& m, std::uint32_t) {
        m.WriteU8(kState + 0x5D, 2);
        throw std::logic_error("opaque Wii routine failed");
    };
    MustThrow<std::logic_error>([&] {
        (void)ApplyRigidBodyOnEndFrame(late_failure, kBody, 1.f, true, cb);
    });
    assert(late_failure.ReadOnly().ReadU8(kState + 0x5D) == 0);
    assert(RigidBodyFlags(late_failure.ReadOnly(), kBody) == 0x040C);

    auto inactive = Fixture(2, 0x040C, kCollider, 0);
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnEndFrame(inactive, kBody, 0.f, false, cb);
    });
    assert(RigidBodyFlags(inactive.ReadOnly(), kBody) == 0x040C);

    auto no_world_callback = Fixture(1);
    cb.resolve_world_position = [](WiiMutableSnapshot&, std::uint32_t) {
        return kWorldPosition;
    };
    MustThrow<std::invalid_argument>([&] {
        (void)ApplyRigidBodyOnEndFrame(no_world_callback, kBody, 0.f, false, cb);
    });
    assert(RigidBodyFlags(no_world_callback.ReadOnly(), kBody) == 0x040C);
}

void TestSnapshotWriteByteBounds() {
    auto s = Fixture();
    s.WriteU8(kState + 0x5D, 255);
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 255);
    MustThrow<std::out_of_range>([&] { s.WriteU8(0, 3); });
    MustThrow<std::out_of_range>([&] { s.WriteU8(0xFFFFFFFF, 4); });
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 255);
}
} // namespace

int main() {
    TestAllActiveCallbacksInSourceOrder();
    TestCollisionPassAndEmptyBranches();
    TestInactiveWorldPositionSynchronization();
    TestMissingCallbacksAreAtomic();
    TestSnapshotWriteByteBounds();
}
