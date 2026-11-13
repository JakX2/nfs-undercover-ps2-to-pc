#pragma once
// Original-free, bounds-checked decoder for EA/NFS JDLZ version 0x02.
// Decoder only: this does not load VPAK/BUN containers or emulate Wii DI/IOS.
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace nwii::runtime {

struct JdlzResultV10 {
    std::vector<uint8_t> output;
    size_t input_consumed = 0;  // Full declared compressed block size.
    std::string error;
    explicit operator bool() const { return error.empty(); }
};

inline uint32_t jdlz_le32_v10(const uint8_t* p) {
    return uint32_t(p[0]) | (uint32_t(p[1]) << 8) |
           (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
}

// Embedded blocks are supported: the source span may contain subsequent data.
// Caller advances by input_consumed, not by the bytes read before the final
// decompressed byte. Real NFS files may include 1-2 unused trailing flag bytes.
inline JdlzResultV10 decode_jdlz_v10(std::span<const uint8_t> source,
                                     size_t max_output = 256u * 1024u * 1024u) {
    auto fail = [](const char* msg) {
        JdlzResultV10 result;
        result.error = msg;
        return result;
    };
    if (source.size() < 16) return fail("JDLZ block shorter than header");
    static constexpr uint8_t magic[8] = {'J','D','L','Z',0x02,0x10,0,0};
    for (size_t i = 0; i < 8; ++i)
        if (source[i] != magic[i]) return fail("unsupported JDLZ magic/version");
    const size_t decoded_size = jdlz_le32_v10(source.data() + 8);
    const size_t packed_size = jdlz_le32_v10(source.data() + 12);
    if (packed_size < 16 || packed_size > source.size())
        return fail("JDLZ compressed length exceeds provided bytes");
    if (decoded_size > max_output) return fail("JDLZ output exceeds configured limit");
    JdlzResultV10 result;
    result.output.resize(decoded_size);
    size_t in_pos = 16, out_pos = 0;
    unsigned flags1 = 1, flags2 = 1;
    while (out_pos < decoded_size) {
        if (flags1 == 1) {
            if (in_pos >= packed_size) return fail("truncated JDLZ flag stream 1");
            flags1 = unsigned(source[in_pos++]) | 0x100u;
        }
        if (flags2 == 1) {
            if (in_pos >= packed_size) return fail("truncated JDLZ flag stream 2");
            flags2 = unsigned(source[in_pos++]) | 0x100u;
        }
        if (flags1 & 1u) {
            if (packed_size - in_pos < 2) return fail("truncated JDLZ back-reference");
            const unsigned a = source[in_pos++];
            const unsigned b = source[in_pos++];
            size_t length, distance;
            if (flags2 & 1u) {
                length = (b | ((a & 0xf0u) << 4u)) + 3u;
                distance = (a & 0x0fu) + 1u;
            } else {
                length = (a & 0x1fu) + 3u;
                distance = (b | ((a & 0xe0u) << 3u)) + 17u;
            }
            if (distance > out_pos) return fail("JDLZ back-reference precedes output");
            if (length > decoded_size - out_pos) return fail("JDLZ copy exceeds output");
            // Byte-wise copy deliberately permits overlapping LZ77 references.
            for (size_t i = 0; i < length; ++i)
                result.output[out_pos + i] = result.output[out_pos + i - distance];
            out_pos += length;
            flags2 >>= 1u;
        } else {
            if (in_pos >= packed_size) return fail("truncated JDLZ literal");
            result.output[out_pos++] = source[in_pos++];
        }
        flags1 >>= 1u;
    }
    result.input_consumed = packed_size;
    return result;
}

} // namespace nwii::runtime
