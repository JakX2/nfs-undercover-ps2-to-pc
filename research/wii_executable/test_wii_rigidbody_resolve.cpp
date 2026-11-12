#include "wii_rigidbody_resolve.hpp"

#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t kBody = 0x80060000u;
constexpr std::uint32_t kState = kBody + 0x300u;

void Put32(std::vector<std::uint8_t>& b, std::size_t off, std::uint32_t v) {
    assert(off + 4 <= b.size());
    b[off] = std::uint8_t(v >> 24);
    b[off + 1] = std::uint8_t(v >> 16);
    b[off + 2] = std::uint8_t(v >> 8);
    b[off + 3] = std::uint8_t(v);
}

WiiMutableSnapshot Fixture(std::uint8_t status=1, std::uint16_t flags=0x2002) {
    std::vector<std::uint8_t> raw(0x700, 0);
    Put32(raw, 0x70, kBody + 0x180);
    Put32(raw, 0x180, kState);
    raw[0x300 + 0x5D] = status;
    raw[0x300 + 0x1C] = std::uint8_t(flags >> 8);
    raw[0x300 + 0x1D] = std::uint8_t(flags);
    return WiiMutableSnapshot({{kBody, std::move(raw)}});
}

bool Equal(Vec3 a, Vec3 b) {
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

template <class E, class F> void MustThrow(F f) {
    bool caught = false;
    try { f(); } catch (const E&) { caught = true; }
    assert(caught);
}

void TestWakeAndForceAccumulation() {
    auto s = Fixture();
    RigidBodySetForce(s, kBody, {1.f, 2.f, 3.f});
    RigidBodySetTorque(s, kBody, {6.f, 7.f, 8.f});
    int detaches = 0;
    auto detach = [&](WiiMutableSnapshot& next, std::uint32_t body) {
        assert(body == kBody);
        ++detaches;
        const auto m = next.ReadOnly();
        assert(m.ReadU8(kState + 0x5D) == 0);
        assert(RigidBodyFlags(m, kBody) == 0x2042u);
        // Simulate original Detach's potential flag side effect.
        next.WriteU16BE(kState + 0x1C, 0x2040u);
        // Accumulation must be performed AFTER the Detach callback.
        RigidBodySetForce(next, body, {10.f, 20.f, 30.f});
    };
    assert(WiiRigidBodyBaseResolveForce(s, kBody, {4.f, -5.f, 6.f}, detach)
           == WiiResolveResult::accumulated);
    assert(detaches == 1);
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 0);
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x2040);
    assert(Equal(RigidBodyForce(s.ReadOnly(), kBody), {14.f, 15.f, 36.f}));
    assert(Equal(RigidBodyTorque(s.ReadOnly(), kBody), {6.f, 7.f, 8.f}));
}

void TestTorqueAccumulationAndIdempotentWake() {
    auto s = Fixture(0, 0x0000);
    RigidBodySetForce(s, kBody, {1.f, 2.f, 3.f});
    RigidBodySetTorque(s, kBody, {-1.f, 2.f, -3.f});
    int calls = 0;
    auto detach = [&](WiiMutableSnapshot& next, std::uint32_t body) {
        assert(body == kBody);
        ++calls;
        assert(next.ReadOnly().ReadU8(kState + 0x5D) == 0);
        assert((RigidBodyFlags(next.ReadOnly(), body) & 0x40u) != 0);
    };
    for (int i = 0; i < 2; ++i)
        assert(WiiRigidBodyBaseResolveTorque(s, kBody, {2.f, -4.f, 6.f}, detach)
               == WiiResolveResult::accumulated);
    assert(calls == 2); // Original calls Detach even when status==0.
    assert(Equal(RigidBodyTorque(s.ReadOnly(), kBody), {3.f, -6.f, 9.f}));
    assert(Equal(RigidBodyForce(s.ReadOnly(), kBody), {1.f, 2.f, 3.f}));
}

void TestStatusTwoIsStrictNoOp() {
    auto s = Fixture(2, 0x0123);
    RigidBodySetForce(s, kBody, {1.f, 2.f, 3.f});
    RigidBodySetTorque(s, kBody, {4.f, 5.f, 6.f});
    int calls = 0;
    auto detach = [&](WiiMutableSnapshot&, std::uint32_t) { ++calls; };
    assert(WiiRigidBodyBaseResolveForce(s, kBody, {100.f, 0.f, 0.f}, detach)
           == WiiResolveResult::ignored_status_two);
    assert(WiiRigidBodyBaseResolveTorque(s, kBody, {100.f, 0.f, 0.f}, {})
           == WiiResolveResult::ignored_status_two);
    assert(calls == 0);
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 2);
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x0123);
    assert(Equal(RigidBodyForce(s.ReadOnly(), kBody), {1.f, 2.f, 3.f}));
    assert(Equal(RigidBodyTorque(s.ReadOnly(), kBody), {4.f, 5.f, 6.f}));
}

void TestErrorsAreTransactional() {
    auto s = Fixture(1, 0x0002);
    MustThrow<std::invalid_argument>([&] {
        (void)WiiRigidBodyBaseResolveForce(s, kBody, {1.f, 0.f, 0.f}, {});
    });
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 1);
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x0002);
    MustThrow<std::logic_error>([&] {
        (void)WiiRigidBodyBaseResolveTorque(s, kBody, {1.f, 0.f, 0.f},
            [](WiiMutableSnapshot& next, std::uint32_t) {
                next.WriteU16BE(kState + 0x1C, 0xFFFF);
                throw std::logic_error("unrecovered Wii Detach failed");
            });
    });
    assert(s.ReadOnly().ReadU8(kState + 0x5D) == 1);
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x0002);
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseResolveForce(s, 0, {1.f, 2.f, 3.f},
            [](WiiMutableSnapshot&, std::uint32_t) {});
    });
    assert(RigidBodyFlags(s.ReadOnly(), kBody) == 0x0002);
}
} // namespace

int main() {
    TestWakeAndForceAccumulation();
    TestTorqueAccumulationAndIdempotentWake();
    TestStatusTwoIsStrictNoOp();
    TestErrorsAreTransactional();
}
