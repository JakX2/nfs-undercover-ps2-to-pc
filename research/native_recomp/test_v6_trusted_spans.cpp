// Source-only synthetic trust-boundary regression for NWiiRecomp.
#include "analyzer/analyzer.h"
#include "loader/loader.h"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace nwii;
static void require(bool ok, const char* what) {
  if (!ok) throw std::runtime_error(what);
}
static void put_be(std::vector<uint8_t>& bytes, size_t offset, uint32_t value) {
  bytes.at(offset) = (value >> 24) & 0xff;
  bytes.at(offset+1) = (value >> 16) & 0xff;
  bytes.at(offset+2) = (value >> 8) & 0xff;
  bytes.at(offset+3) = value & 0xff;
}
static loader::Executable fixture() {
  loader::Executable result{};
  result.entry_point = 0x80001000;
  loader::Section text{};
  text.address=0x80001000; text.size=0x80; text.is_text=true; text.is_bss=false;
  text.data.resize(text.size, 0);
  // A normal return at every legitimate entry, including an inside-function
  // address (a valid compiler helper entry). The fake strings are non-code.
  for (auto off : {0u, 0x10u, 0x14u, 0x30u}) put_be(text.data,off,0x4e800020);
  const char* literal="Metrowerks Target Resident Kernel";
  for (unsigned i=0;i<32;++i) text.data[0x20+i] = uint8_t(literal[i]);
  // Preserve real return immediately after overlapping data-string text.
  put_be(text.data,0x30u,0x4e800020);
  result.sections.push_back(std::move(text));
  loader::Section data{};
  data.address=0x80002000;data.size=0x10;data.is_text=false;data.is_bss=false;
  data.data.resize(16, 0);
  put_be(data.data,0,0x80001020); // fake pointer into text-resident string
  put_be(data.data,4,0x80001030); // real code pointer
  result.sections.push_back(std::move(data));
  return result;
}
int main() {
  unsigned tests=0;
  auto exe=fixture();
  const std::vector<uint32_t> roots={0x80001010,0x80001014,0x80001020,0x80001030};
  {
    analyzer::Analyzer unfiltered(exe);
    unfiltered.analyze(roots);
    require(unfiltered.get_functions().count(0x80001020),"unfiltered baseline should find fake function");
    ++tests;
  }
  {
    analyzer::Analyzer filtered(exe);
    // Overlapping and touching segments are permitted, merged internally.
    filtered.set_trusted_code_spans({{0x80001010,0x80001014},
                                     {0x80001000,0x80001004},
                                     {0x80001014,0x80001018},
                                     {0x80001030,0x80001034}});
    filtered.analyze(roots);
    const auto& funcs=filtered.get_functions();
    require(!funcs.count(0x80001020),"string must never become function"); ++tests;
    require(funcs.count(0x80001000),"entrypoint must survive"); ++tests;
    require(funcs.count(0x80001010),"first legit root must survive"); ++tests;
    require(funcs.count(0x80001014),"interior function target must survive"); ++tests;
    require(funcs.count(0x80001030),"function after literal must survive"); ++tests;
    require(funcs.size() == 4,"unexpected function filtered in or out"); ++tests;
  }
  {
    analyzer::Analyzer filtered(exe);
    try {filtered.set_trusted_code_spans({});throw std::runtime_error("empty spans silently accepted");}
    catch(const std::invalid_argument&) {++tests;}
    try {filtered.set_trusted_code_spans({{0x80001006,0x80001010}});throw std::runtime_error("misalignment silently accepted");}
    catch(const std::invalid_argument&) {++tests;}
    try {filtered.set_trusted_code_spans({{0x80001010,0x80001000}});throw std::runtime_error("reversed range silently accepted");}
    catch(const std::invalid_argument&) {++tests;}
  }
  std::cout << "PASS: " << tests << " independent analyzer trust-boundary assertions\n";
}
