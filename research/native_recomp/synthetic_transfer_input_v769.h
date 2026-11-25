#pragma once
#include <array>
#include <cstdint>
// Independent syntax-only fixture. No original executable code or addresses.
inline constexpr uint32_t H=0x80004000u,C=0x80005000u,D=0x80006000u,Q=0x80007000u,S=0x80008000u,R=0x80009000u;
inline constexpr std::array<uint32_t,18> caller{};
inline constexpr std::array<uint32_t,108> transfer_words{};
inline constexpr std::array<uint32_t,5> disable_words{};
inline constexpr std::array<uint32_t,9> irq_restore_words{};
inline constexpr std::array<uint32_t,7> save_words{},restore_words{};
