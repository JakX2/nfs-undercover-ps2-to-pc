// Original-free synthetic CPU-context tests; not proof of hardware-exact behavior.
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <limits>
#include "runtime/cpu_context.h"

namespace nwii::runtime {
uint32_t g_watch_addr = 0;
void watch_hit(uint32_t, uint32_t, int) {}
void GX_WGPIPE_Write8(uint8_t) {}
void GX_WGPIPE_Write16(uint16_t) {}
void GX_WGPIPE_Write32(uint32_t) {}
void GX_WGPIPE_WriteF32(float) {}
void GX_WGPIPE_WriteF64(double) {}
uint16_t HW_Reg_Read16(uint32_t) { return 0; }
uint32_t HW_Reg_Read32(uint32_t) { return 0; }
void HW_Reg_Write16(uint32_t, uint16_t) {}
void HW_Reg_Write32(uint32_t, uint32_t) {}
}
static void check(bool pass, const char* msg) {
  if (!pass) throw std::runtime_error(msg);
}
int main() {
  using nwii::runtime::CPUContext;
  int n = 0;
  for (int i=0; i<64; ++i) {
    const int expected=i<32?i:i-64;
    check(CPUContext::signed_gqr_scale6(i)==expected, "sign extension"); ++n;
  }
  CPUContext c;
  constexpr uint32_t addr=0x80000100u;
  c.mmu.write8(addr, 6);
  // Load signed scale 0x3f = -1, so 6 * 2^1 = 12.
  c.gqr[0]=(0x3Fu << 24)|(4u<<16);
  c.psq_load(2,addr,1,0);
  check(c.fpr[2]==12.0 && c.ps1[2]==1.0, "negative GQR load scale W1"); ++n;
  c.gqr[0]=(0x20u << 24)|(4u<<16); // -32
  c.psq_load(2,addr,1,0);
  check(c.fpr[2]==25769803776.0, "negative GQR load scale -32"); ++n;
  c.gqr[1]=(0x3Fu<<8)|4u;
  c.fpr[3]=12; c.ps1[3]=20;
  c.psq_store(3,addr+8,0,1);
  check(c.mmu.read8(addr+8)==6 && c.mmu.read8(addr+9)==10,"signed GQR store scale"); ++n;
  c.gqr[1]=(2u<<8)|4u;
  c.fpr[3]=4;
  c.psq_store(3,addr+12,1,1);
  check(c.mmu.read8(addr+12)==16,"positive store scale"); ++n;
  c.fpr[5]=4; c.ps1[5]=9;
  c.ps_rsqrte(5,5); // same src/dst must preserve both input lanes
  check(std::abs(c.fpr[5]-0.5)<0.000001 && std::abs(c.ps1[5]-1.0/3.0)<1e-6,"rsqrte both lanes"); ++n;
  c.fpr[6]=4; c.ps1[6]=8;
  c.ps_res(6,6);
  check(c.fpr[6]==0.25 && c.ps1[6]==0.125,"reciprocal both lanes"); ++n;
  c.fpr[7]=-4; c.ps1[7]=0;
  c.ps_rsqrte(7,7);
  check(std::isnan(c.fpr[7]) && std::isinf(c.ps1[7]) && c.ps1[7]>0,"rsqrte negative and zero"); ++n;
  std::cout << "PASS: " << n << " synthetic CPU runtime assertions (not Wii-exact)\n";
}
