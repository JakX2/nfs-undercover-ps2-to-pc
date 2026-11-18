#pragma once
#include <array>
#include <cstdint>
// Wholly synthetic handler to exercise the native MMIO and IRQ lifecycle.
// r10 is the IPC MMIO base, r11 is the Hollywood W1C bit. The handler
// acknowledges the observed Y flag, clears the IRQ latch and executes rfi.
namespace synthetic_irq_roundtrip {
inline constexpr uint32_t Entry=0x80004000u,Resume=Entry+12u,Stop=Entry+16u,Vector=0x80000500u;
inline constexpr std::array<uint32_t,5> words={
  (32u<<26)|(8u<<21)|(10u<<16)|4u,       // lwz r8,4(r10)
  (36u<<26)|(8u<<21)|(10u<<16)|4u,       // stw r8,4(r10)
  (36u<<26)|(11u<<21)|(10u<<16)|0x30u,   // stw r11,0x30(r10)
  (14u<<26)|(6u<<21)|(6u<<16)|1u,        // addi r6,r6,1
  0x4c000064u                            // rfi
};
inline constexpr auto bytes=[]{
    std::array<uint8_t,words.size()*4> v{};
    for(unsigned i=0;i<words.size();++i)
        for(unsigned j=0;j<4;++j)v[i*4+j]=uint8_t(words[i]>>(24u-j*8u));
    return v;
}();
}
