#include "attrib_memory.hpp"

#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace undercover::attrib {
namespace {
constexpr std::size_t kMaxRegions = 1024;
constexpr std::size_t kMaxRegionBytes = 16 * 1024 * 1024;
constexpr std::size_t kMaxTotalBytes = 64 * 1024 * 1024;

std::uint32_t AddFieldOffset(std::uint32_t address, std::uint32_t offset) {
    // Null is a Wii sentinel rather than a readable address. A non-null but
    // missing address fails closed through the address space lookup.
    if (address == 0 || address > std::numeric_limits<std::uint32_t>::max() - offset)
        throw std::out_of_range("invalid Wii object address");
    return address + offset;
}
}  // namespace

WiiAddressSpace::WiiAddressSpace(std::vector<WiiMemoryRegion> regions)
    : regions_(std::move(regions)) {
    if (regions_.size() > kMaxRegions)
        throw std::invalid_argument("too many Wii memory regions");
    std::sort(regions_.begin(), regions_.end(),
              [](const WiiMemoryRegion& a, const WiiMemoryRegion& b) {
                  return a.base < b.base;
              });
    std::uint64_t last_end = 0;
    std::size_t total = 0;
    for (const auto& r : regions_) {
        const std::uint64_t end = std::uint64_t(r.base) + r.bytes.size();
        if (r.base == 0 || r.bytes.empty() || r.bytes.size() > kMaxRegionBytes ||
            end > (std::uint64_t(1) << 32) ||
            std::uint64_t(r.base) < last_end ||
            r.bytes.size() > kMaxTotalBytes - total)
            throw std::invalid_argument("invalid or overlapping Wii address range");
        last_end = end;
        total += r.bytes.size();
    }
}

const WiiMemoryRegion& WiiAddressSpace::Locate(std::uint32_t address,
                                               std::size_t length) const {
    // An aligned 32-bit load may not straddle two region boundaries.
    if (!address || !length || length > 4 ||
        std::uint64_t(address) + length > (std::uint64_t(1) << 32))
        throw std::out_of_range("invalid Wii read range");
    auto it = std::upper_bound(regions_.begin(), regions_.end(), address,
        [](std::uint32_t addr, const WiiMemoryRegion& r) { return addr < r.base; });
    if (it == regions_.begin())
        throw std::out_of_range("unmapped Wii address");
    --it;
    const std::size_t relative = std::size_t(address - it->base);
    if (relative > it->bytes.size() || length > it->bytes.size() - relative)
        throw std::out_of_range("Wii read exceeds mapped region");
    return *it;
}

std::uint8_t WiiAddressSpace::ReadU8(std::uint32_t address) const {
    const auto& r = Locate(address, 1);
    return r.bytes[address - r.base];
}

std::uint32_t WiiAddressSpace::ReadU32BE(std::uint32_t address) const {
    if (address & 3)
        throw std::out_of_range("unaligned PowerPC lwz address");
    const auto& r = Locate(address, 4);
    const std::size_t offset = address - r.base;
    return (std::uint32_t(r.bytes[offset]) << 24) |
           (std::uint32_t(r.bytes[offset + 1]) << 16) |
           (std::uint32_t(r.bytes[offset + 2]) << 8) |
           std::uint32_t(r.bytes[offset + 3]);
}

std::uint32_t AttributeCollectionAddress(const WiiAddressSpace& m,
                                          std::uint32_t attribute) {
    // GetCollection__Q26Attrib9AttributeCFv at 0x8007B2BC.
    return m.ReadU32BE(AddFieldOffset(attribute, 4));
}

std::uint32_t AttributeDescriptorAddress(const WiiAddressSpace& m,
                                          std::uint32_t attribute) {
    // Descriptor pointer is observed by IsValid and GetKey at Wii +0x08.
    return m.ReadU32BE(AddFieldOffset(attribute, 8));
}

bool AttributeIsValid(const WiiAddressSpace& m, std::uint32_t attribute) {
    // IsValid__Q26Attrib9AttributeCFv at 0x8007B208.
    return AttributeDescriptorAddress(m, attribute) != 0;
}

bool AttributeIsMutable(const WiiAddressSpace& m, std::uint32_t attribute) {
    // IsMutable__Q26Attrib9AttributeCFv at 0x8007B21C.
    const auto collection = AttributeCollectionAddress(m, attribute);
    if (!collection || !AttributeDescriptorAddress(m, attribute)) return false;
    return m.ReadU32BE(AddFieldOffset(collection, 0x1C)) == 0;
}

std::uint32_t AttributeKey(const WiiAddressSpace& m, std::uint32_t attribute) {
    // GetKey__Q26Attrib9AttributeCFv at 0x8007B24C.
    const auto descriptor = AttributeDescriptorAddress(m, attribute);
    if (!descriptor || !(m.ReadU8(AddFieldOffset(descriptor, 0x0B)) & 0x80u))
        return 0;
    return m.ReadU32BE(descriptor);
}

std::uint32_t CollectionKey(const WiiAddressSpace& m, std::uint32_t collection) {
    // GetCollectionKey__6AttribFPCQ26Attrib10Collection at 0x8007A970.
    return collection ? m.ReadU32BE(AddFieldOffset(collection, 0x10)) : 0;
}

std::uint32_t CollectionClassKey(const WiiAddressSpace& m, std::uint32_t collection) {
    // GetCollectionClassKey__6AttribFPCQ26Attrib10Collection at 0x8007A988.
    if (!collection) return 0;
    const auto class_address = m.ReadU32BE(AddFieldOffset(collection, 0x14));
    return class_address ? m.ReadU32BE(class_address) : 0;
}

std::uint32_t CollectionParentAddress(const WiiAddressSpace& m, std::uint32_t collection) {
    // GetCollectionParent__6AttribFPCQ26Attrib10Collection at 0x8007A9B4.
    return collection ? m.ReadU32BE(AddFieldOffset(collection, 0x0C)) : 0;
}

std::uint32_t CollectionSourceAddress(const WiiAddressSpace& m, std::uint32_t collection) {
    // GetCollectionSource__6AttribFPCQ26Attrib10Collection at 0x8007A9E8.
    // The original dereferences unconditionally; unmapped/null addresses fail.
    return m.ReadU32BE(AddFieldOffset(collection, 0x1C));
}

bool CollectionSourceIsVault(const WiiAddressSpace& m, std::uint32_t collection,
                             std::uint32_t vault) {
    // IsSourceVault__6AttribFPCQ26Attrib10CollectionPCQ26Attrib5Vault
    // at 0x8007A9D4: pointer value equality, including zero.
    return CollectionSourceAddress(m, collection) == vault;
}

TweakFields DecodeTweakFields(const WiiAddressSpace& m, std::uint32_t attribute,
                              std::uint32_t element_index,
                              std::string_view attribute_name) {
    const auto collection = AttributeCollectionAddress(m, attribute);
    return {CollectionClassKey(m, collection), CollectionKey(m, collection),
            AttributeKey(m, attribute), element_index, attribute_name};
}

}  // namespace undercover::attrib
