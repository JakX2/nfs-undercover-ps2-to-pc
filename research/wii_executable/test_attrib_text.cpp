#include "attrib_text.hpp"

#include <cassert>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>

int main() {
    using namespace undercover::attrib;
    const char* digits = "0123456789abcdef";
    for (int nibble = 0; nibble < 16; ++nibble)
        assert(NibbleChar(static_cast<std::uint8_t>(nibble)) == digits[nibble]);
    assert(ValueToText(nullptr, 0).empty());
    const std::uint8_t bytes[] = {0, 1, 16, 0xA5, 0xFF};
    assert(ValueToText(bytes, 5) == "000110a5ff");
    bool rejected = false;
    try { (void) ValueToText(nullptr, 1); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);
    const char string_sample[] = {'A', static_cast<char>(0x80), '\0', 'Z'};
    assert(CopyString(string_sample, sizeof(string_sample)) ==
           std::string(string_sample, 2));
    assert(CopyString("", 1).empty());
    assert(CopyString(nullptr, 0).empty());
    rejected = false;
    try { (void) CopyString(nullptr, 1); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);
    rejected = false;
    try { (void) CopyString("hi", 2); }
    catch (const std::length_error&) { rejected = true; }
    assert(rejected);
    assert(IntToString(0) == "0");
    assert(IntToString(9) == "9");
    assert(IntToString(10) == "10");
    assert(IntToString(1000000000u) == "1000000000");
    assert(IntToString(std::numeric_limits<std::uint32_t>::max()) == "4294967295");
    std::uint32_t seed = 0x9E3779B9;
    for (int i = 0; i < 10000; ++i) {
        seed = seed * 1664525u + 1013904223u;
        assert(IntToString(seed) == std::to_string(seed));
    }
}
