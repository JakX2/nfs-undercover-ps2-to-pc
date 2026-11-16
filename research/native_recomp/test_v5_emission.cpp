// Purely synthetic NWiiRecomp instruction-emission tests. No game code.
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"

using namespace nwii;
static uint32_t ppc4(uint32_t xo10, uint32_t d, uint32_t b) {
  return (4u << 26) | (d << 21) | (b << 11) | (xo10 << 1);
}
static uint32_t ppc_spr(uint32_t xo, uint32_t d, uint32_t spr) {
  return (31u << 26) | (d << 21) | ((spr & 31u) << 16) | ((spr >> 5) << 11) | (xo << 1);
}
static void check(const std::string& got, const std::string& needle) {
  if (got.find(needle) == std::string::npos)
    throw std::runtime_error("Expected emitted text: " + needle + "; actual: " + got.substr(0,1000));
}
int main() {
  loader::Executable empty;
  analyzer::Analyzer analyzer(empty);
  recomp::Recompiler tr(analyzer);
  auto emit = [&](uint32_t op) {
    analyzer::Function fun{};
    fun.start_address = 0x80010000;
    fun.end_address = 0x80010004;
    fun.instructions.push_back({fun.start_address, op});
    return tr.generate_function_cpp(fun);
  };
  unsigned count = 0;
  check(emit(ppc4(26, 2, 3)), "ctx.ps_rsqrte(2, 3)"); ++count;
  check(emit(ppc4(24, 8, 9)), "ctx.ps_res(8, 9)"); ++count;
  for (uint32_t spr = 272; spr <= 275; ++spr) {
    check(emit(ppc_spr(339, 13, spr)), "ctx.gpr[13] = ctx.sprg[" + std::to_string(spr - 272) + "]"); ++count;
    check(emit(ppc_spr(467, 13, spr)), "ctx.sprg[" + std::to_string(spr - 272) + "] = ctx.gpr[13]"); ++count;
  }
  std::cout << "PASS: " << count << " synthetic emitted-instruction cases\n";
}
