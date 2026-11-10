#include "attrib_tweak.hpp"
#include "attrib_text.hpp"

#include <stdexcept>
#include <string>

namespace undercover::attrib {
namespace {

// Deliberate host-side safety policy. The Wii routine constructs into a
// fixed-size stack buffer without validating the caller's byte count.
constexpr std::size_t kMaxPacketBytes = 1024 * 1024;

void AppendU32BigEndianHex(std::string& output, std::uint32_t value) {
    const std::uint8_t bytes[4] = {
        static_cast<std::uint8_t>(value >> 24),
        static_cast<std::uint8_t>(value >> 16),
        static_cast<std::uint8_t>(value >> 8),
        static_cast<std::uint8_t>(value),
    };
    output += ValueToText(bytes, 4);
}

void CheckMessageSize(std::size_t prefix_size, std::size_t value_size) {
    if (prefix_size > kMaxPacketBytes ||
        value_size > (kMaxPacketBytes - prefix_size) / 2)
        throw std::length_error("tweak packet exceeds host-side safety bound");
}

}  // namespace

std::string EncodeTweakPacketPrefix(const TweakFields& fields) {
    // Named Wii PPC source: EncodeTweakPacketPrefix at 0x8007AEDC.
    // Original helper serializes three four-byte keys with ValueToText, then
    // builds a path using CopyString and a decimal element index.
    // Its fixed protocol prefix and suffix come from the Wii .data/.sdata.
    std::string out("AttribSys.rev\\");
    AppendU32BigEndianHex(out, fields.collection_class_key);
    out += '\\';
    AppendU32BigEndianHex(out, fields.collection_key);
    out += '\\';
    AppendU32BigEndianHex(out, fields.attribute_key);
    out += '\\';
    out += IntToString(fields.element_index);
    out += '\\';
    // Original CopyString stops at the first NUL. This host API accepts a
    // string_view, but rejects embedded NUL to prevent ambiguous packets.
    if (fields.attribute_name.find('\0') != std::string_view::npos)
        throw std::invalid_argument("attribute name contains NUL");
    if (fields.attribute_name.size() > kMaxPacketBytes - out.size() - 4)
        throw std::length_error("attribute name exceeds packet budget");
    out.append(fields.attribute_name.data(), fields.attribute_name.size());
    out += "\\[]:";
    return out;
}

std::string EncodeTweakPacket(const TweakFields& fields,
                              const std::uint8_t* data, std::size_t size) {
    // Named Wii PPC source: TweakAttribute at 0x8007AFF8.
    if (size && !data) throw std::invalid_argument("null nonempty payload");
    auto packet = EncodeTweakPacketPrefix(fields);
    CheckMessageSize(packet.size(), size);
    packet += ValueToText(data, size);
    return packet;
}

std::string TweakAttribute(const TweakFields& fields,
                           const std::uint8_t* data, std::size_t size,
                           const TweakMessageSender& sender) {
    auto packet = EncodeTweakPacket(fields, data, size);
    if (sender) sender(packet);
    return packet;
}

}  // namespace undercover::attrib
