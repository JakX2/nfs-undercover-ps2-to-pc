#include "attrib_memory.hpp"

#include <cassert>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

using namespace undercover::attrib;

static void Write32(std::vector<std::uint8_t>& b, std::size_t off,
                    std::uint32_t value) {
    assert(off + 4 <= b.size());
    b[off] = std::uint8_t(value >> 24);
    b[off + 1] = std::uint8_t(value >> 16);
    b[off + 2] = std::uint8_t(value >> 8);
    b[off + 3] = std::uint8_t(value);
}

static WiiAddressSpace Example(bool has_class=true, bool has_descriptor=true,
                               std::uint8_t flag=0x80, std::uint32_t source=0) {
    const std::uint32_t base = 0x80010000u;
    std::vector<std::uint8_t> raw(0x100, 0);
    // Attribute @base+0x00, Collection @base+0x40,
    // descriptor @base+0x80, class @base+0xC0.
    Write32(raw, 0x04, base + 0x40);
    Write32(raw, 0x08, has_descriptor ? base + 0x80 : 0);
    Write32(raw, 0x40 + 0x0c, base + 0xF0);
    Write32(raw, 0x40 + 0x10, 0x11223344);
    Write32(raw, 0x40 + 0x14, has_class ? base + 0xC0 : 0);
    Write32(raw, 0x40 + 0x1c, source);
    Write32(raw, 0x80, 0xA1B2C3D4);
    raw[0x80 + 0x0b] = flag;
    Write32(raw, 0xC0, 0x01020304);
    return WiiAddressSpace({{base, std::move(raw)}});
}

template <class Err, class Callable> static void ExpectThrows(Callable f) {
    bool caught = false;
    try { f(); } catch (const Err&) { caught = true; }
    assert(caught);
}

int main() {
    constexpr std::uint32_t a = 0x80010000u;
    constexpr std::uint32_t c = a + 0x40;
    const auto m = Example();
    assert(AttributeCollectionAddress(m, a) == c);
    assert(AttributeDescriptorAddress(m, a) == a + 0x80);
    assert(AttributeIsValid(m, a));
    assert(AttributeIsMutable(m, a));
    assert(AttributeKey(m, a) == 0xA1B2C3D4);
    assert(CollectionKey(m, c) == 0x11223344);
    assert(CollectionClassKey(m, c) == 0x01020304);
    assert(CollectionParentAddress(m, c) == a + 0xF0);
    assert(CollectionSourceAddress(m, c) == 0);
    assert(CollectionSourceIsVault(m, c, 0));
    assert(!CollectionSourceIsVault(m, c, 1));
    assert(CollectionClassKey(m, 0) == 0);
    assert(CollectionKey(m, 0) == 0);
    assert(CollectionParentAddress(m, 0) == 0);
    ExpectThrows<std::out_of_range>([&] { (void)CollectionSourceAddress(m, 0); });
    const auto fields = DecodeTweakFields(m, a, 42, "Speed");
    assert(fields.collection_class_key == 0x01020304);
    assert(fields.collection_key == 0x11223344);
    assert(fields.attribute_key == 0xA1B2C3D4);
    const std::uint8_t payload[] = {0x00, 0xAA, 0xFF};
    assert(EncodeTweakPacket(fields, payload, sizeof(payload)) ==
           "AttribSys.rev\\01020304\\11223344\\a1b2c3d4\\42\\Speed\\[]:00aaff");

    const auto absent_class = Example(false);
    assert(CollectionClassKey(absent_class, c) == 0);
    const auto absent_descriptor = Example(true, false);
    assert(!AttributeIsValid(absent_descriptor, a));
    assert(!AttributeIsMutable(absent_descriptor, a));
    assert(AttributeKey(absent_descriptor, a) == 0);
    assert(DecodeTweakFields(absent_descriptor, a, 0, "x").attribute_key == 0);
    for (int flag = 0; flag < 256; ++flag) {
        const auto candidate = Example(true, true, static_cast<std::uint8_t>(flag));
        assert(AttributeKey(candidate, a) == ((flag & 0x80) ? 0xA1B2C3D4u : 0));
    }
    const auto readonly = Example(true, true, 0x80, a + 0xE0);
    assert(!AttributeIsMutable(readonly, a));
    assert(CollectionSourceIsVault(readonly, c, a + 0xE0));

    ExpectThrows<std::out_of_range>([&] { (void)m.ReadU8(0x80000000u); });
    ExpectThrows<std::out_of_range>([&] { (void)m.ReadU32BE(a + 1); });
    ExpectThrows<std::out_of_range>([&] { (void)m.ReadU32BE(a + 0xFD); });
    ExpectThrows<std::out_of_range>([&] { (void)m.ReadU32BE(0xfffffffc); });
    ExpectThrows<std::invalid_argument>([] { (void)WiiAddressSpace({{0, {1}}}); });
    ExpectThrows<std::invalid_argument>([] { (void)WiiAddressSpace({{0x8000, {1}}, {0x8000, {2}}}); });
    ExpectThrows<std::invalid_argument>([] { (void)WiiAddressSpace({{0xfffffffe, {1, 2, 3}}}); });
    ExpectThrows<std::invalid_argument>([] { (void)WiiAddressSpace({{0x8000, {}}}); });
    ExpectThrows<std::invalid_argument>([] {
        (void)WiiAddressSpace({{0x8000, std::vector<std::uint8_t>(16*1024*1024+1)}});
    });
    WiiAddressSpace segmented({{0x80002000, {5, 6, 7, 8}}, {0x80001000, {1, 2, 3, 4}}});
    assert(segmented.ReadU32BE(0x80001000) == 0x01020304);
    assert(segmented.ReadU32BE(0x80002000) == 0x05060708);
    ExpectThrows<std::out_of_range>([&] { (void)segmented.ReadU32BE(0x80001004); });
}
