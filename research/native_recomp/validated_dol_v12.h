#pragma once
// Original-free, bounded DOL section-table parser for Wii/GC native startup.
// This validates the DOL's shape; it does not execute copyrighted game code.
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace nwii::loader {
struct ValidatedDolSectionV12 {
    uint32_t file_offset = 0;
    uint32_t guest_address = 0;
    uint32_t size = 0;
    bool executable = false;
    bool is_bss = false;
};
struct ValidatedDolV12 {
    uint32_t entry_point = 0;
    std::vector<ValidatedDolSectionV12> sections;
};
namespace dol_v12_detail {
inline uint32_t be32(const uint8_t* p) {
    return (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) |
           (uint32_t(p[2]) << 8) | uint32_t(p[3]);
}
inline bool in_guest_memory(uint32_t addr, uint32_t size) {
    const uint64_t end = uint64_t(addr) + size;
    return (addr >= 0x80000000u && end <= 0x81800000ull) ||
           (addr >= 0x90000000u && end <= 0x94000000ull);
}
inline bool overlaps(uint64_t a, uint64_t length_a, uint64_t b, uint64_t length_b) {
    return a < b + length_b && b < a + length_a;
}
} // namespace dol_v12_detail

inline bool parse_validated_dol_v12(std::span<const uint8_t> bytes,
                                    ValidatedDolV12& output, std::string& error) {
    using namespace dol_v12_detail;
    ValidatedDolV12 parsed;
    error.clear();
    auto fail = [&](const char* msg) { error = msg; return false; };
    if (bytes.size() < 0x100u) return fail("DOL shorter than 0x100-byte header");
    if (bytes.size() > 128u * 1024u * 1024u) return fail("DOL file exceeds size limit");
    struct Region { uint64_t start; uint64_t size; };
    std::vector<Region> file_regions;
    std::vector<Region> guest_regions;
    for (unsigned category = 0; category < 2; ++category) {
        const unsigned count = category == 0 ? 7 : 11;
        const unsigned file_base = category == 0 ? 0x00 : 0x1c;
        const unsigned addr_base = category == 0 ? 0x48 : 0x64;
        const unsigned size_base = category == 0 ? 0x90 : 0xac;
        for (unsigned i = 0; i < count; ++i) {
            const uint32_t file_offset = be32(bytes.data() + file_base + i * 4);
            const uint32_t address = be32(bytes.data() + addr_base + i * 4);
            const uint32_t length = be32(bytes.data() + size_base + i * 4);
            if (file_offset == 0 && length == 0) continue;
            if (file_offset == 0 || length == 0) return fail("partially empty DOL section");
            if ((file_offset & 3u) || (address & 3u)) return fail("unaligned DOL section");
            if (file_offset < 0x100u || uint64_t(file_offset) + length > bytes.size())
                return fail("DOL section lies outside file");
            if (!in_guest_memory(address, length)) return fail("DOL section exceeds guest RAM");
            for (const auto& other : file_regions)
                if (overlaps(file_offset,length,other.start,other.size))
                    return fail("overlapping DOL file sections");
            for (const auto& other : guest_regions)
                if (overlaps(address,length,other.start,other.size))
                    return fail("overlapping DOL guest sections");
            file_regions.push_back({file_offset,length});
            guest_regions.push_back({address,length});
            parsed.sections.push_back({file_offset,address,length,category==0,false});
        }
    }
    if (parsed.sections.empty()) return fail("no DOL sections");
    const uint32_t bss_addr = be32(bytes.data() + 0xd8);
    const uint32_t bss_size = be32(bytes.data() + 0xdc);
    if (bss_size != 0) {
        if ((bss_addr & 3u) || !in_guest_memory(bss_addr,bss_size))
            return fail("DOL BSS is unaligned or outside guest RAM");
        // DOL BSS can legally encompass initialized data sections. Wii
        // startup zeros BSS first and then copies initialized text/data,
        // restoring those bytes. Do not reject this common layout.
        parsed.sections.push_back({0,bss_addr,bss_size,false,true});
    }
    parsed.entry_point = be32(bytes.data() + 0xe0);
    if ((parsed.entry_point & 3u) != 0) return fail("DOL entry point unaligned");
    bool entry_in_text = false;
    for (const auto& sec : parsed.sections)
        if (sec.executable && parsed.entry_point >= sec.guest_address &&
            uint64_t(parsed.entry_point) < uint64_t(sec.guest_address) + sec.size)
            entry_in_text = true;
    if (!entry_in_text) return fail("DOL entry point not inside a text section");
    output = std::move(parsed); // no partial output on failure
    return true;
}
} // namespace nwii::loader
