#!/usr/bin/env python3
"""Dispatch only to emitted instruction runs; exact function roots win."""
import argparse
from pathlib import Path
FILE=Path('nWiiRecomp/src/recompiler.cpp')
BOUNDS_OLD='''      if (!is_hle) {
        out << "    {0x" << std::hex << std::uppercase << start_addr << ", 0x"
            << func.end_address << ", " << func_name << "},\\n";
      }'''
BOUNDS_NEW='''      if (!is_hle) {
        // A function's min/max interval can contain holes or other roots.
        std::set<uint32_t> emitted_labels;
        for (const auto &inst : func.instructions)
          emitted_labels.insert(inst.address);
        auto it = emitted_labels.begin();
        while (it != emitted_labels.end()) {
          const uint32_t first = *it;
          uint32_t last = first;
          ++it;
          while (it != emitted_labels.end() && *it > last && *it - last == 4u) {
            last = *it;
            ++it;
          }
          out << "    {0x" << std::hex << std::uppercase << first << ", 0x"
              << (uint64_t(last) + 4u) << ", " << func_name << "},\\n";
        }
      }'''
STRUCT_OLD='''    out << "struct FuncBound { uint32_t start; uint32_t end; "
           "void(*func)(CPUContext&); };\\n";'''
STRUCT_NEW='''    out << "struct FuncBound { uint32_t start; uint64_t end; "
           "void(*func)(CPUContext&); };\\n";'''
CASES_OLD='''      if (!is_hle) {
        for (const auto &inst : func.instructions) {
          ppc::Instruction ppc_inst(inst.opcode);'''
CASES_NEW='''      if (!is_hle) {
        std::set<uint32_t> native_labels;
        for (const auto &inst : func.instructions) native_labels.insert(inst.address);
        // Never let a resume label shadow a separately analyzed entry.
        auto claim_resume = [&](uint32_t addr) {
          return !analyzer_.get_functions().count(addr) &&
                 native_labels.count(addr) && emitted_cases.insert(addr).second;
        };
        for (const auto &inst : func.instructions) {
          ppc::Instruction ppc_inst(inst.opcode);'''
PAIRS=((BOUNDS_OLD,BOUNDS_NEW),(STRUCT_OLD,STRUCT_NEW),(CASES_OLD,CASES_NEW),
       ('if (emitted_cases.insert(ret_addr).second) {','if (claim_resume(ret_addr)) {'),
       ('if (emitted_cases.insert(inst.address).second) {','if (claim_resume(inst.address)) {'),
       ('if (emitted_cases.insert(jump_target).second) {','if (claim_resume(jump_target)) {'),
       ('if (target >= fb.start && target < fb.end) {','if (!(target & 3u) && target >= fb.start && target < fb.end) {'))
def rewrite(source):
    if all(source.count(b)==2 and a not in source for a,b in PAIRS):return source
    if not all(source.count(a)==2 and b not in source for a,b in PAIRS):raise ValueError('unknown or mixed dispatcher geometry')
    out=source
    for a,b in PAIRS:out=out.replace(a,b)
    back=out
    for a,b in reversed(PAIRS):back=back.replace(b,a)
    if back!=source:raise ValueError('roundtrip')
    return out
def apply(root):
    path=root/FILE
    if path.is_symlink():raise ValueError('symlink')
    old=path.read_text(encoding='utf-8');new=rewrite(old)
    if old==new:return False
    path.write_text(new,encoding='utf-8');return True
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V445_EXACT_DISPATCH installed=1 changed={int(apply(a.root))}')
