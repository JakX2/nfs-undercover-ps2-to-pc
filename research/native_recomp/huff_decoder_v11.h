#pragma once
// Independent, original-free EA HUFF/EAC decoder for NFS Wii resource data.
// Handles HUFF v1 wrapper and EAC 30FB, 32FB and 34FB bitstreams.
// Not a Wii HLE hook and not an asset container parser.
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace nwii::runtime {
struct HuffResultV11 {
    std::vector<uint8_t> output;
    size_t input_consumed = 0;
    std::string error;
    explicit operator bool() const { return error.empty(); }
};

namespace huff_v11_detail {
inline uint32_t le32(const uint8_t* p) {
    return uint32_t(p[0]) | (uint32_t(p[1]) << 8) |
           (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
}
class BitReader {
public:
    explicit BitReader(std::span<const uint8_t> data) : data_(data) {}
    bool read(unsigned bits, uint32_t& value) {
        if (bits > 30 || bits > data_.size() * 8 - position_) return false;
        uint32_t result = 0;
        for (unsigned i = 0; i < bits; ++i) {
            result = (result << 1) | ((data_[position_ >> 3] >> (7 - (position_ & 7))) & 1u);
            ++position_;
        }
        value = result;
        return true;
    }
    bool variable(uint32_t& value) {
        unsigned width = 2;
        uint32_t bit = 0;
        while (true) {
            if (!read(1, bit)) return false;
            if (bit) break;
            if (++width > 29) return false;
        }
        if (!read(width, value)) return false;
        value += (uint32_t(1) << width) - 4u;
        return true;
    }
    size_t bits_consumed() const { return position_; }
private:
    std::span<const uint8_t> data_;
    size_t position_ = 0;
};
} // namespace huff_v11_detail

inline HuffResultV11 decode_huff_v11(std::span<const uint8_t> source,
                                     size_t max_output = 256u * 1024u * 1024u) {
    auto fail = [](const char* why) { HuffResultV11 r; r.error = why; return r; };
    static constexpr uint8_t magic[8] = {'H','U','F','F',1,16,0,0};
    if (source.size() < 16) return fail("HUFF wrapper header truncated");
    for (size_t i=0; i<8; ++i)
        if (source[i] != magic[i]) return fail("unsupported HUFF wrapper magic/version");
    const size_t output_size = huff_v11_detail::le32(source.data()+8);
    const size_t packed_size = huff_v11_detail::le32(source.data()+12);
    if (output_size > max_output) return fail("HUFF output exceeds size limit");
    if (packed_size < 6 || packed_size > source.size()-16)
        return fail("HUFF compressed size outside input");
    huff_v11_detail::BitReader bit(source.subspan(16, packed_size));
    uint32_t method=0;
    if (!bit.read(16, method)) return fail("HUFF method truncated");
    const uint32_t method_base = method & ~0x100u;
    if (method_base != 0x30fbu && method_base != 0x32fbu && method_base != 0x34fbu)
        return fail("unsupported EAC Huffman method");
    uint32_t discarded=0;
    if ((method & 0x100u) && !bit.read(24, discarded))
        return fail("HUFF extended header truncated");
    uint32_t decoded_header=0, esc=0;
    if (!bit.read(24, decoded_header) || !bit.read(8, esc))
        return fail("EAC Huffman size/escape truncated");
    if (decoded_header != output_size) return fail("wrapper and EAC decoded lengths disagree");

    std::array<uint16_t, 17> counts{};
    std::array<uint16_t, 17> first_codes{};
    std::array<uint16_t, 17> first_symbols{};
    uint32_t count_total=0, used_codes=0;
    unsigned max_width=0;
    for (unsigned width=1; width<=16; ++width) {
        uint32_t count=0;
        if (!bit.variable(count)) return fail("truncated EAC code lengths");
        if (count > 256 - count_total) return fail("too many Huffman symbols");
        counts[width] = static_cast<uint16_t>(count);
        count_total += count;
        used_codes = (used_codes << 1) + count;
        if (used_codes > (1u << width)) return fail("oversubscribed Huffman code lengths");
        if (used_codes == (1u << width)) {max_width=width; break;}
    }
    if (!max_width || !count_total) return fail("incomplete Huffman code lengths");

    std::array<bool,256> assigned{};
    std::vector<uint8_t> ordered;
    ordered.reserve(count_total);
    unsigned last=255;
    for (uint32_t i=0; i<count_total; ++i) {
        uint32_t advance=0;
        if (!bit.variable(advance)) return fail("truncated Huffman symbol permutation");
        if (advance >= 256-i) return fail("invalid Huffman symbol permutation");
        uint32_t remaining=advance+1;
        for (unsigned visited=0; visited<256; ++visited) {
            last=(last+1)&255u;
            if (!assigned[last] && --remaining==0) break;
        }
        if (remaining) return fail("failed to place Huffman symbol");
        assigned[last]=true;
        ordered.push_back(static_cast<uint8_t>(last));
    }
    uint32_t next_code=0, next_symbol=0;
    for (unsigned width=1; width<=max_width; ++width) {
        next_code <<= 1;
        first_codes[width] = static_cast<uint16_t>(next_code);
        first_symbols[width] = static_cast<uint16_t>(next_symbol);
        next_code += counts[width];
        next_symbol += counts[width];
    }

    HuffResultV11 result;
    result.output.reserve(output_size);
    while (true) {
        uint32_t code=0, symbol=256;
        for (unsigned width=1; width<=max_width; ++width) {
            uint32_t b=0;
            if (!bit.read(1,b)) return fail("truncated Huffman code");
            code=(code<<1)|b;
            const uint32_t base=first_codes[width];
            if (code>=base && code-base<counts[width]) {
                symbol=ordered[first_symbols[width]+(code-base)];
                break;
            }
        }
        if (symbol==256) return fail("invalid Huffman codeword");
        if (symbol!=esc) {
            if (result.output.size()==output_size) return fail("HUFF literal exceeds decoded length");
            result.output.push_back(static_cast<uint8_t>(symbol));
            continue;
        }
        uint32_t count=0;
        if (!bit.variable(count)) return fail("truncated HUFF escape count");
        if (count==0) {
            uint32_t eos=0;
            if (!bit.read(1,eos)) return fail("truncated HUFF escape/EOS flag");
            if (eos) break;
            uint32_t raw=0;
            if (!bit.read(8,raw)) return fail("truncated HUFF raw byte");
            if (result.output.size()==output_size) return fail("HUFF raw byte exceeds decoded length");
            result.output.push_back(static_cast<uint8_t>(raw));
        } else {
            if (result.output.empty()) return fail("HUFF repeat precedes first byte");
            if (count>output_size-result.output.size()) return fail("HUFF repeat exceeds decoded length");
            result.output.insert(result.output.end(),count,result.output.back());
        }
    }
    if (result.output.size()!=output_size) return fail("HUFF decoded length does not match header");
    uint8_t sum1=0,sum2=0;
    if (method_base==0x32fb) {
        for (auto& b:result.output) { sum1=static_cast<uint8_t>(sum1+b); b=sum1; }
    } else if (method_base==0x34fb) {
        for (auto& b:result.output) {
            sum1=static_cast<uint8_t>(sum1+b);
            sum2=static_cast<uint8_t>(sum2+sum1);
            b=sum2;
        }
    }
    result.input_consumed = 16 + packed_size;
    return result;
}
} // namespace nwii::runtime
