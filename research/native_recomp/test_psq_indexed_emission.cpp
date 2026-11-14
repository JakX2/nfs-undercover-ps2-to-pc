// Source-only regression. Instructions are synthetic; no game binary is used.
#include <cstdint>
#include <iostream>
#include <string>
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"

static uint32_t make_psq(uint32_t xo6, uint32_t fr, uint32_t ra, uint32_t rb, uint32_t w, uint32_t gqr) {
  return (4u << 26) | (fr << 21) | (ra << 16) | (rb << 11) | (w << 10) | (gqr << 7) | (xo6 << 1);
}
static void expect(const std::string& output, const char *fragment) {
  if (output.find(fragment) == std::string::npos) {
    std::cerr << "Expected emitted fragment not found: " << fragment << "\n" << output.substr(0,1500) << "\n";
    std::exit(1);
  }
}
int main() {
  nwii::loader::Executable empty;
  nwii::analyzer::Analyzer analyzer(empty);
  nwii::recomp::Recompiler tr(analyzer);
  int tests = 0;
  auto emit = [&](uint32_t opcode) {
    nwii::analyzer::Function f{};
    f.start_address = 0x80010000;
    f.end_address = 0x80010004;
    f.instructions.push_back({f.start_address, opcode});
    return tr.generate_function_cpp(f);
  };
  auto verify = [&](uint32_t xo, uint32_t ra, uint32_t rb, uint32_t w, uint32_t gqr,
                    const char* fragment) {
    const std::string s = emit(make_psq(xo, 2, ra, rb, w, gqr));
    expect(s, fragment);
    if (s.find("UNIMPLEMENTED Opcode 4") != std::string::npos) {
      std::cerr << "Unexpected opcode trap\n";
      std::exit(1);
    }
    ++tests;
  };
  verify(6,  0, 7, 0, 0, "ctx.psq_load(2, ea, 0, 0)");
  verify(6,  6, 7, 1, 5, "ctx.psq_load(2, ea, 1, 5)");
  verify(7,  6, 7, 0, 0, "ctx.psq_store(2, ea, 0, 0)");
  verify(38, 6, 7, 0, 5, "ctx.gpr[6] = ea;");
  verify(39, 6, 7, 1, 5, "ctx.psq_store(2, ea, 1, 5)");
  verify(39, 0, 7, 0, 0, "Invalid psq_*ux rA=0");
  std::cout << "PASS: " << tests << " indexed paired-single emission checks\n";
}
