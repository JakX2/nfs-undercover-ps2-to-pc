#pragma once
// Independently authored, synthetic Wii SYSCONF image for the native IOS
// read-only guest filesystem. This is NOT a NAND dump or an original game file.
// Public format: https://wiibrew.org/wiki//shared2/sys/SYSCONF
// The original SC SDK routines must still parse and validate the image.
// Do not report successful game initialization from this resource alone.
#include "wii_guest_filesystem.h"
#include <array>
#include <cstdint>
#include <cstring>
#include <memory>
#include <optional>
#include <string_view>

namespace undercover::wii {

struct SysconfImageOptions {
    // Wii SDK option bytes. Defaults model a fresh PC-facing, read-only setup.
    uint8_t language = 1u;        // 1 = English
    uint8_t widescreen = 1u;      // 0 = 4:3; 1 = 16:9
    uint8_t sound = 1u;           // 0 = mono; 1 = stereo; 2 = surround
    uint8_t progressive = 0u;
    uint8_t eurgb60 = 1u;
    uint8_t sensor_bar = 1u;      // 0 = below; 1 = above
    uint8_t rumble = 1u;
    uint8_t speaker_volume = 0x58u;
    uint8_t screen_saver = 1u;
};

class SysconfImage {
public:
    static constexpr uint32_t Size = 0x4000u;
    static constexpr uint32_t LookupBegin = 0x3faeu;
    static constexpr std::string_view Path = "/shared2/sys/SYSCONF";

    // Build a deterministic subset of the console configuration namespace.
    // Missing entries are intentionally left absent: SC must apply its own
    // documented fallback, rather than this layer inventing their values.
    static std::optional<GuestFiles::Bytes> build(const SysconfImageOptions& opts = {}) {
        if (opts.language > 9u || opts.widescreen > 1u || opts.sound > 2u ||
            opts.progressive > 1u || opts.eurgb60 > 1u ||
            opts.sensor_bar > 1u || opts.rumble > 1u || opts.screen_saver > 1u)
            return std::nullopt;

        struct Entry {
            std::string_view name;
            uint8_t value;
            uint16_t lookup; // Lookup slot from the public Wii SYSCONF layout.
        };
        const std::array<Entry,9> settings{{
            {"BT.BAR", opts.sensor_bar, 0x3fb8u},
            {"BT.MOT", opts.rumble, 0x3fbau},
            {"BT.SPKV", opts.speaker_volume, 0x3fbcu},
            {"IPL.AR", opts.widescreen, 0x3ff8u},
            {"IPL.E60", opts.eurgb60, 0x3ffeeu},
            {"IPL.LNG", opts.language, 0x3fe4u},
            {"IPL.PGS", opts.progressive, 0x3fdeu},
            {"IPL.SND", opts.sound, 0x3fd8u},
            {"IPL.SSV", opts.screen_saver, 0x3fdcu}
        }};
        constexpr uint8_t byte_type = 3u;
        GuestFiles::Bytes bytes(Size, 0u);
        std::memcpy(bytes.data(), "SCv0", 4);
        put16(bytes, 4u, uint16_t(settings.size()));
        unsigned cursor = 6u + 2u * (settings.size() + 1u);
        for (unsigned i = 0; i < settings.size(); ++i) {
            const Entry& e = settings[i];
            if (e.name.empty() || e.name.size() > 32u ||
                cursor + e.name.size() + 2u > LookupBegin ||
                e.lookup < LookupBegin || e.lookup + 2u > Size - 4u ||
                (e.lookup & 1u))
                return std::nullopt;
            const unsigned index_location = 6u + i * 2u;
            put16(bytes, index_location, uint16_t(cursor));
            put16(bytes, e.lookup, uint16_t(index_location));
            bytes[cursor++] = uint8_t((byte_type << 5u) | uint8_t(e.name.size() - 1u));
            for (char ch : e.name) bytes[cursor++] = uint8_t(ch);
            bytes[cursor++] = e.value;
        }
        put16(bytes, 6u + 2u * settings.size(), uint16_t(cursor));
        std::memcpy(bytes.data() + (Size - 4u), "SCed", 4);
        return bytes;
    }

    // Explicit owner-controlled mount; duplicates are rejected by GuestFiles.
    // No host filesystem, global settings, or guest status byte are changed.
    static bool add_to(GuestFiles& files, const SysconfImageOptions& opts = {}) {
        auto bytes = build(opts);
        return bytes.has_value() &&
               files.add(std::string(Path), std::move(*bytes));
    }

private:
    static void put16(GuestFiles::Bytes& data, unsigned offset, uint16_t value) {
        data[offset] = uint8_t(value >> 8u);
        data[offset + 1u] = uint8_t(value);
    }
};

} // namespace undercover::wii
