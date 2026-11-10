#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <string_view>

namespace undercover::attrib {

// The original Wii function obtains these keys from its Attribute/Collection
// objects. Our portable representation intentionally avoids Wii object layout.
struct TweakFields {
    std::uint32_t collection_class_key;
    std::uint32_t collection_key;
    std::uint32_t attribute_key;
    std::uint32_t element_index;
    std::string_view attribute_name;
};

// Reconstructed packet format from the named Wii PPC function family. Keys
// serialize as *big-endian memory bytes*, matching original Wii ValueToText.
std::string EncodeTweakPacketPrefix(const TweakFields& fields);
std::string EncodeTweakPacket(const TweakFields& fields,
                              const std::uint8_t* data, std::size_t size);

// The Wii code invokes a global callback only when installed. The portable
// counterpart returns the built packet and optionally calls a host callback.
using TweakMessageSender = std::function<void(std::string_view)>;
std::string TweakAttribute(const TweakFields& fields,
                           const std::uint8_t* data, std::size_t size,
                           const TweakMessageSender& sender = {});

}  // namespace undercover::attrib
