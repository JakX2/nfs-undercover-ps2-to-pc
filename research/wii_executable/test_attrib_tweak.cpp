#include "attrib_tweak.hpp"

#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

using namespace undercover::attrib;

int main() {
    TweakFields sample{0x11223344, 0xA1B2C3D4, 0x01020304, 42, "Speed"};
    const std::string prefix = "AttribSys.rev\\11223344\\a1b2c3d4\\01020304\\42\\Speed\\[]:";
    assert(EncodeTweakPacketPrefix(sample) == prefix);
    const std::uint8_t bytes[] = {0x00, 0x10, 0x7f, 0x80, 0xff};
    assert(EncodeTweakPacket(sample, bytes, 5) == prefix + "00107f80ff");
    assert(EncodeTweakPacket(sample, nullptr, 0) == prefix);

    int callbacks = 0;
    std::string received;
    auto result = TweakAttribute(sample, bytes, 5, [&](std::string_view value) {
        ++callbacks;
        received.assign(value);
    });
    assert(callbacks == 1 && received == result && result == prefix + "00107f80ff");
    (void)TweakAttribute(sample, bytes, 5);
    assert(callbacks == 1);

    sample.collection_class_key = 0;
    sample.collection_key = 0xffffffff;
    sample.attribute_key = 0;
    sample.element_index = 0xffffffff;
    sample.attribute_name = "";
    assert(EncodeTweakPacket(sample, bytes, 1) ==
           "AttribSys.rev\\00000000\\ffffffff\\00000000\\4294967295\\\\[]:00");

    bool rejected = false;
    try { (void)EncodeTweakPacket(sample, nullptr, 1); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);

    sample.attribute_name = std::string_view("bad\0key", 7);
    rejected = false;
    try { (void)EncodeTweakPacketPrefix(sample); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);

    sample.attribute_name = "long";
    std::vector<std::uint8_t> too_large(1024 * 1024, 0xff);
    rejected = false;
    try { (void)EncodeTweakPacket(sample, too_large.data(), too_large.size()); }
    catch (const std::length_error&) { rejected = true; }
    assert(rejected);

    const std::string long_name(1024 * 1024, 'x');
    sample.attribute_name = long_name;
    rejected = false;
    try { (void)EncodeTweakPacketPrefix(sample); }
    catch (const std::length_error&) { rejected = true; }
    assert(rejected);
}
