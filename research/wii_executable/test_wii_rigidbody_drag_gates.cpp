#include "wii_rigidbody_drag_gates.hpp"
#include <cassert>
#include <cstdint>
using undercover::vehicle::SelectDoDragPaths;
int main() {
    // Exhaustive 16-bit flags: unrelated bits must not influence the gates.
    for (std::uint32_t bits = 0; bits <= 0xffffu; ++bits) {
        const auto flags = static_cast<std::uint16_t>(bits);
        const auto selected = SelectDoDragPaths(flags);
        const bool inhibited = (flags & 0x0002u) != 0;
        assert(selected.first == (!inhibited && (flags & 0x0800u) != 0));
        assert(selected.second == (!inhibited && (flags & 0x0020u) != 0));
        const auto unrelated = static_cast<std::uint16_t>(flags ^ 0xf7ddu);
        const auto other = SelectDoDragPaths(unrelated);
        assert(selected.first == other.first);
        assert(selected.second == other.second);
    }
    assert(!SelectDoDragPaths(0).first && !SelectDoDragPaths(0).second);
    assert(SelectDoDragPaths(0x0820).first && SelectDoDragPaths(0x0820).second);
    assert(!SelectDoDragPaths(0x0822).first && !SelectDoDragPaths(0x0822).second);
}
