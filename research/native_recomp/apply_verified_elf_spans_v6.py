#!/usr/bin/env python3
"""Opt-in source backed code-span gating for NWiiRecomp's PPC analyzer.

Public patch contains no game material. Requires CSV function start/size values
validated against the exact Wii ELF/DOL pair and never commits the CSV itself.
"""
from pathlib import Path
import argparse

H = Path('nWiiAnalyzer/include/analyzer/analyzer.h')
S = Path('nWiiAnalyzer/src/analyzer.cpp')

def sub_once(s: str, needle: str, replacement: str, what: str) -> str:
    if replacement in s:
        return s
    if s.count(needle) != 1:
        raise RuntimeError(f'{what}: upstream layout mismatch ({s.count(needle)} anchors)')
    return s.replace(needle, replacement, 1)

def apply(root: Path):
    hp, sp = root/H, root/S
    h,s = hp.read_text(), sp.read_text()
    h = sub_once(h, '#include <queue>\n', '#include <queue>\n#include <utility>\n', 'header include')
    h = sub_once(h, '    void analyze(const std::vector<uint32_t>& additional_roots = {});',
                 '    void set_trusted_code_spans(std::vector<std::pair<uint32_t, uint32_t>> spans);\n'
                 '    void analyze(const std::vector<uint32_t>& additional_roots = {});', 'public setter')
    h = sub_once(h, '    bool read_instruction(uint32_t address, uint32_t& out_inst) const;',
                 '    bool trusted_instruction(uint32_t address) const;\n'
                 '    bool read_instruction(uint32_t address, uint32_t& out_inst) const;', 'private helper')
    h = sub_once(h, '    const loader::Executable& executable_;',
                 '    bool trusted_code_filter_enabled_ = false;\n'
                 '    std::vector<std::pair<uint32_t, uint32_t>> trusted_code_spans_;\n'
                 '    const loader::Executable& executable_;', 'private state')

    anchor='''Analyzer::Analyzer(const loader::Executable &executable)
    : executable_(executable) {}
'''
    implementation='''Analyzer::Analyzer(const loader::Executable &executable)
    : executable_(executable) {}

void Analyzer::set_trusted_code_spans(std::vector<std::pair<uint32_t, uint32_t>> spans) {
  // The source should be ELF sized STT_FUNC spans. Half-open [start,end).
  // Fail closed for invalid or absent spans. No filter is applied unless this
  // method is explicitly called, preserving generic analyzer behavior.
  if (spans.empty()) throw std::invalid_argument("empty trusted code span set");
  for (const auto& [start, end] : spans)
    if (start >= end || (start & 3) || (end & 3))
      throw std::invalid_argument("invalid or unaligned trusted code span");
  std::sort(spans.begin(), spans.end());
  std::vector<std::pair<uint32_t, uint32_t>> merged;
  for (const auto& p : spans) {
    if (!merged.empty() && p.first <= merged.back().second)
      merged.back().second = std::max(merged.back().second, p.second);
    else merged.push_back(p);
  }
  trusted_code_spans_ = std::move(merged);
  trusted_code_filter_enabled_ = true;
}

bool Analyzer::trusted_instruction(uint32_t address) const {
  if (!trusted_code_filter_enabled_) return true;
  auto it = std::upper_bound(trusted_code_spans_.begin(),
                             trusted_code_spans_.end(), address,
                             [](uint32_t a, const auto& range) { return a < range.first; });
  if (it == trusted_code_spans_.begin()) return false;
  --it;
  return address >= it->first && uint64_t(address) + 4 <= it->second;
}
'''
    s = sub_once(s, anchor, implementation, 'trusted methods')
    s = sub_once(s, '#include <cstring>\n', '#include <cstring>\n#include <stdexcept>\n', 'stdexcept include')
    s = sub_once(s, 'bool Analyzer::read_instruction(uint32_t address, uint32_t &out_inst) const {',
                 'bool Analyzer::read_instruction(uint32_t address, uint32_t &out_inst) const {\n'
                 '  if (!trusted_instruction(address)) return false;', 'instruction guard')
    s = sub_once(s, 'bool Analyzer::is_text_address(uint32_t address) const {',
                 'bool Analyzer::is_text_address(uint32_t address) const {\n'
                 '  if (!trusted_instruction(address)) return false;', 'text guard')
    s = sub_once(s, '''    uint32_t func_start = function_queue.front();
    function_queue.pop();

    if (functions_.find(func_start) != functions_.end())''',
                 '''    uint32_t func_start = function_queue.front();
    function_queue.pop();
    // Branch targets / pointer scans can refer to data stored in text sections.
    // Never create an empty function at an excluded source address.
    if (!is_text_address(func_start)) continue;

    if (functions_.find(func_start) != functions_.end())''', 'queued root guard')
    # All validations are complete before either file is touched.
    if hp.read_text() != h: hp.write_text(h)
    if sp.read_text() != s: sp.write_text(s)
    print('Updated NWii analyzer with optional trusted ELF code spans')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('upstream_root',type=Path)
    args=p.parse_args()
    apply(args.upstream_root)
