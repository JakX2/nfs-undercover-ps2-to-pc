#pragma once

#include "attrib_tweak.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace undercover::attrib {

// Private, synthetic or owner-local snapshot of 32-bit Wii virtual memory.
// All pointers below remain uint32_t *Wii addresses*, never host pointers.
struct WiiMemoryRegion {
    std::uint32_t base;
    std::vector<std::uint8_t> bytes;
};

class WiiAddressSpace {
public:
    explicit WiiAddressSpace(std::vector<WiiMemoryRegion> regions);
    std::uint8_t ReadU8(std::uint32_t address) const;
    std::uint32_t ReadU32BE(std::uint32_t address) const;

private:
    const WiiMemoryRegion& Locate(std::uint32_t address,
                                   std::size_t length) const;
    std::vector<WiiMemoryRegion> regions_;
};

// Offsets verified independently in the original Wii PowerPC assembly.
std::uint32_t AttributeCollectionAddress(const WiiAddressSpace& m, std::uint32_t attribute);
std::uint32_t AttributeDescriptorAddress(const WiiAddressSpace& m, std::uint32_t attribute);
bool AttributeIsValid(const WiiAddressSpace& m, std::uint32_t attribute);
bool AttributeIsMutable(const WiiAddressSpace& m, std::uint32_t attribute);
std::uint32_t AttributeKey(const WiiAddressSpace& m, std::uint32_t attribute);
std::uint32_t CollectionKey(const WiiAddressSpace& m, std::uint32_t collection);
std::uint32_t CollectionClassKey(const WiiAddressSpace& m, std::uint32_t collection);
std::uint32_t CollectionParentAddress(const WiiAddressSpace& m, std::uint32_t collection);
std::uint32_t CollectionSourceAddress(const WiiAddressSpace& m, std::uint32_t collection);
bool CollectionSourceIsVault(const WiiAddressSpace& m, std::uint32_t collection,
                             std::uint32_t vault);

// Bridges original Wii object offsets to the portable message serializer.
TweakFields DecodeTweakFields(const WiiAddressSpace& m, std::uint32_t attribute,
                              std::uint32_t element_index,
                              std::string_view attribute_name);

}  // namespace undercover::attrib
