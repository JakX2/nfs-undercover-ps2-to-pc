#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace undercover::attrib {
// Behaviorally reconstructed from named Wii PPC functions in NfsMWRelease.elf.
// These provide safe, portable interfaces, not binary-identical original ABI.
char NibbleChar(std::uint8_t nibble);
std::string ValueToText(const std::uint8_t* source, std::size_t size);
std::string IntToString(std::uint32_t value);
}  // namespace undercover::attrib
