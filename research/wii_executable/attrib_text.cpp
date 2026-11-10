#include "attrib_text.hpp"

#include <stdexcept>

namespace undercover::attrib {

// Wii symbol: NibbleChar__6AttribFUc, 0x8007ADAC, 28 bytes.
char NibbleChar(std::uint8_t nibble) {
    // The original function does not mask or clamp its input; the callers
    // normally provide 0..15. Preserve the low byte of the computed ASCII.
    const unsigned int c = (nibble <= 9) ? unsigned(nibble) + 48u
                                         : unsigned(nibble) + 87u;
    return static_cast<char>(static_cast<std::uint8_t>(c));
}

// Wii symbol: ValueToText__6AttribFPCvUiPc, 0x8007ADC8.
std::string ValueToText(const std::uint8_t* source, std::size_t size) {
    if (!source && size) throw std::invalid_argument("null nonempty source");
    std::string output;
    if (size > output.max_size() / 2) throw std::length_error("oversized input");
    output.reserve(size * 2);
    for (std::size_t i = 0; i < size; ++i) {
        const std::uint8_t value = source[i];
        output.push_back(NibbleChar(value >> 4));
        output.push_back(NibbleChar(value & 15));
    }
    return output;
}

// Wii symbol: CopyString__6AttribFPcPCc, 0x8007AE38, 44 bytes.
// Original PPC loop reads each signed-tested source byte and writes it
// unchanged to destination; the final NUL byte is always written.
// Our portable host interface returns a string instead of an unchecked
// caller-owned output buffer, requiring its terminator within a bounded span.
std::string CopyString(const char* source, std::size_t available) {
    if (!source) {
        if (available) throw std::invalid_argument("null nonempty source");
        return {};
    }
    for (std::size_t i = 0; i < available; ++i) {
        if (source[i] == '\0') return std::string(source, i);
    }
    throw std::length_error("unterminated source in bounded span");
}

// Wii symbol: IntToString__6AttribFPcUi, 0x8007AE64, 120 bytes.
std::string IntToString(std::uint32_t value) {
    std::string result;
    bool started = false;
    for (std::uint32_t divisor = 1'000'000'000; divisor > 0; divisor /= 10) {
        const std::uint32_t digit = value / divisor;
        if (started || digit) {
            result.push_back(static_cast<char>('0' + digit));
            value -= digit * divisor;
            started = true;
        }
    }
    if (!started) result.push_back('0');
    return result;
}

}  // namespace undercover::attrib
