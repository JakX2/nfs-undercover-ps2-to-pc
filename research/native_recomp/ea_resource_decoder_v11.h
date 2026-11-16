#pragma once
// Original-free optional resource decompression dispatcher. Do not replace
// guest Wii DVD reads with decoded bytes: original PPC routines expect .LZC.
#include "huff_decoder_v11.h"
#include "jdlz_decoder_v10.h"
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace nwii::runtime {
enum class EaCompressionV11 { Unknown, Jdlz, Huff };
struct EaResourceResultV11 {
    EaCompressionV11 compression = EaCompressionV11::Unknown;
    std::vector<uint8_t> output;
    size_t input_consumed = 0;
    std::string error;
    explicit operator bool() const {return error.empty();}
};
inline EaResourceResultV11 decode_ea_resource_v11(
    std::span<const uint8_t> data, size_t max_output=256u*1024u*1024u) {
    EaResourceResultV11 result;
    if(data.size()<4) {result.error="resource header too short";return result;}
    if(data[0]=='J'&&data[1]=='D'&&data[2]=='L'&&data[3]=='Z') {
        result.compression=EaCompressionV11::Jdlz;
        auto decoded=decode_jdlz_v10(data,max_output);
        result.output=std::move(decoded.output);
        result.input_consumed=decoded.input_consumed;
        result.error=std::move(decoded.error);
    } else if(data[0]=='H'&&data[1]=='U'&&data[2]=='F'&&data[3]=='F') {
        result.compression=EaCompressionV11::Huff;
        auto decoded=decode_huff_v11(data,max_output);
        result.output=std::move(decoded.output);
        result.input_consumed=decoded.input_consumed;
        result.error=std::move(decoded.error);
    } else {
        result.error="resource is neither JDLZ nor HUFF";
    }
    return result;
}
} // namespace nwii::runtime
