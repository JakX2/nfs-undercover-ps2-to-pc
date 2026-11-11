#include "wii_rigidbody_transform.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

using namespace undercover::vehicle;

namespace {
constexpr std::uint32_t body = 0x80060000u;
constexpr std::uint32_t state = body + 0x400u;

void Set32(std::vector<std::uint8_t>& data, std::size_t off, std::uint32_t v) {
    assert(off + 4 <= data.size());
    data[off] = std::uint8_t(v >> 24);
    data[off + 1] = std::uint8_t(v >> 16);
    data[off + 2] = std::uint8_t(v >> 8);
    data[off + 3] = std::uint8_t(v);
}

bool Near(float x, float y) {
    return std::abs(x - y) < 0.00003f;
}
void Check(Vec3 got, Vec3 expected) {
    assert(Near(got.x, expected.x));
    assert(Near(got.y, expected.y));
    assert(Near(got.z, expected.z));
}
template<class Error, class Fn> void MustThrow(Fn f) {
    bool failed = false;
    try { f(); } catch (const Error&) { failed = true; }
    assert(failed);
}

WiiMutableSnapshot Fixture() {
    std::vector<std::uint8_t> data(0x900, 0);
    Set32(data, 0x70, body + 0x200);
    Set32(data, 0x200, state);
    WiiMutableSnapshot m({{body, std::move(data)}});
    m.WriteMatrix4BE(state + 0x70, {
        1.f,0.f,0.f,0.f,
        0.f,1.f,0.f,0.f,
        0.f,0.f,1.f,0.f,
        0.f,0.f,0.f,1.f
    });
    RigidBodySetPosition(m, body, {10.f, 20.f, 30.f});
    return m;
}

void TestIdentityAndTranslationFlag() {
    const auto m = Fixture();
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {1.f, 2.f, 3.f}, false),
          {1.f, 2.f, 3.f});
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {1.f, 2.f, 3.f}, true),
          {11.f, 22.f, 33.f});
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {0.f, 0.f, 0.f}, true),
          {10.f, 20.f, 30.f});
}

void TestOriginalMatrixConventions() {
    auto m = Fixture();
    // Wii quaternion-to-matrix convention at +0x70:
    // +90 degrees about Z: X axis moves to positive Y.
    m.WriteMatrix4BE(state + 0x70, {
        0.f, 1.f, 0.f, 0.f,
       -1.f, 0.f, 0.f, 0.f,
        0.f, 0.f, 1.f, 0.f,
        0.f, 0.f, 0.f, 1.f
    });
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {1.f, 0.f, 0.f}, false),
          {0.f, 1.f, 0.f});
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {0.f, 1.f, 0.f}, false),
          {-1.f, 0.f, 0.f});
    Check(WiiRigidBodyBaseConvertLocalToWorld(m.ReadOnly(), body,
                                             {2.f, 3.f, 4.f}, true),
          {7.f, 22.f, 34.f});
}

void TestOnlyNineWiiMatrixWordsRequired() {
    std::vector<std::uint8_t> b(0x74, 0);
    Set32(b, 0x70, body + 0x200);
    std::vector<std::uint8_t> wrapper(4, 0);
    Set32(wrapper, 0, state);
    WiiMutableSnapshot minimal({
        {body, std::move(b)},
        {body+0x200, std::move(wrapper)},
        {state+0x70, std::vector<std::uint8_t>(12, 0)},
        {state+0x80, std::vector<std::uint8_t>(12, 0)},
        {state+0x90, std::vector<std::uint8_t>(12, 0)}
    });
    minimal.WriteVec3BE(state + 0x70, {1.f, 0.f, 0.f});
    minimal.WriteVec3BE(state + 0x80, {0.f, 1.f, 0.f});
    minimal.WriteVec3BE(state + 0x90, {0.f, 0.f, 1.f});

    // The original transforms successfully without the final row,
    // the 4th column, or the position when translation=false.
    Check(WiiRigidBodyBaseConvertLocalToWorld(minimal.ReadOnly(), body,
                                             {4.f, 5.f, 6.f}, false),
          {4.f, 5.f, 6.f});
    // Unlike ConvertLocalToWorld, the original inverse method's
    // transpose loop reads all 16 source-matrix words.
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseConvertWorldToLocal(minimal.ReadOnly(), body,
                                                  {4.f, 5.f, 6.f}, false);
    });
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseConvertLocalToWorld(minimal.ReadOnly(), body,
                                                  {4.f, 5.f, 6.f}, true);
    });
    MustThrow<std::out_of_range>([&] {
        (void)WiiRigidBodyBaseConvertLocalToWorld(minimal.ReadOnly(), 0,
                                                  {1.f, 2.f, 3.f}, false);
    });
}

void TestWorldToLocalTransposeAndTranslation() {
    auto m = Fixture();
    Check(WiiRigidBodyBaseConvertWorldToLocal(m.ReadOnly(), body,
                                             {11.f, 22.f, 33.f}, true),
          {1.f, 2.f, 3.f});
    Check(WiiRigidBodyBaseConvertWorldToLocal(m.ReadOnly(), body,
                                             {11.f, 22.f, 33.f}, false),
          {11.f, 22.f, 33.f});

    m.WriteMatrix4BE(state + 0x70, {
         0.f, 1.f, 0.f, 0.f,
        -1.f, 0.f, 0.f, 0.f,
         0.f, 0.f, 1.f, 0.f,
         0.f, 0.f, 0.f, 1.f
    });
    Check(WiiRigidBodyBaseConvertWorldToLocal(m.ReadOnly(), body,
                                             {7.f, 22.f, 34.f}, true),
          {2.f, 3.f, 4.f});
    Check(WiiRigidBodyBaseConvertWorldToLocal(m.ReadOnly(), body,
                                             {0.f, 1.f, 0.f}, false),
          {1.f, 0.f, 0.f});

    // A non-orthonormal matrix distinguishes row/column selection
    // independently from the quaternion-based rotation example.
    m.WriteMatrix4BE(state + 0x70, {
         2.f, 3.f, 4.f, 99.f,
         5.f, 6.f, 7.f, 98.f,
         8.f, 9.f,10.f, 97.f,
        11.f,12.f,13.f, 96.f
    });
    Check(WiiRigidBodyBaseConvertWorldToLocal(m.ReadOnly(), body,
                                             {1.f, 2.f, 3.f}, false),
          {20.f, 38.f, 56.f});
}

} // namespace

int main() {
    TestIdentityAndTranslationFlag();
    TestOriginalMatrixConventions();
    TestOnlyNineWiiMatrixWordsRequired();
    TestWorldToLocalTransposeAndTranslation();
}
