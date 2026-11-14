#!/usr/bin/env python3
"""Original-free V26 regression tests for the PowerPC \`sc\` guest-PC emitter.

Exercises the exact upstream source transformation, fail-closed behavior and
emitted C++ for several guest PCs. No Wii executable, extracted code or game
assets are needed. Run alongside apply_syscall_pc_v26.py with Python 3 and g++.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from apply_syscall_pc_v26 import OLD, NEW, apply


def ensure(condition, message):
    if not condition:
        raise AssertionError(message)


def reject_without_writes(root, original):
    source = root / 'nWiiRecomp/src/recompiler.cpp'
    source.write_text(original, encoding='utf-8')
    try:
        apply(root)
    except ValueError:
        pass
    else:
        raise AssertionError('unknown/ambiguous emitter source was accepted')
    ensure(source.read_text(encoding='utf-8') == original,
           'rejected patch unexpectedly modified the upstream source')


def compile_run(compiler, source, output, path):
    path.write_text(source, encoding='utf-8')
    binary = path.with_suffix('')
    build = subprocess.run([compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                            str(path), '-o', str(binary)], capture_output=True,
                           text=True, timeout=30)
    if build.returncode:
        raise RuntimeError('C++ compilation failed: ' + build.stderr)
    result = subprocess.run([str(binary)], check=True, capture_output=True,
                            text=True, timeout=10)
    return result.stdout if output else None


def test_emitted_cpp(root, compiler):
    # Compile and run the actual C++ insertion carried in the Python patch.
    # The first stage runs the transformed emitter for three known addresses.
    emitter = r'''#include <cstdint>
#include <iomanip>
#include <iostream>
#include <sstream>
struct PPCInstruction { int opcode() const { return 17; } };
struct AddressedInstruction { uint32_t address; };
int main() {
  for (uint32_t address : {0x805206B4u, 0x80004058u, 0xFFFFFFFFu}) {
    PPCInstruction ppc_inst{};
    AddressedInstruction inst{address};
    std::ostringstream out;
    if (false) {
''' + NEW + r'''  }
    std::cout << "BEGIN " << std::hex << std::uppercase << address << "\n"
              << out.str() << "END\n";
  }
}
'''
    emitted = compile_run(compiler, emitter, True, root / 'emitter.cpp')
    expected = ('805206B4', '80004058', 'FFFFFFFF')
    for address in expected:
        block = emitted.split('BEGIN ' + address + '\n', 1)[1].split('END\n', 1)[0]
        pc = 'ctx.pc = 0x' + address + ';'
        ensure(block.count(pc) == 1, 'wrong or missing sc guest PC: ' + address)
        ensure(block.count('nwii::runtime::handle_syscall(ctx);') == 1,
               'sc handler omitted or duplicated: ' + address)
        ensure(block.index(pc) < block.index('handle_syscall(ctx)'),
               'sc handler observes stale PC: ' + address)
    ensure(emitted.count('BEGIN ') == len(expected), 'unexpected emitted blocks')

    # The second C++ binary executes the actual emitted statements. Every test
    # starts with an intentionally stale branch-return address in ctx.pc.
    calls = []
    for address in expected:
        block = emitted.split('BEGIN ' + address + '\n', 1)[1].split('END\n', 1)[0]
        calls.append('  ctx.pc = 0x805206ACu;\n' + block +
                     '  if (observed != 0x' + address + 'u) return 1;\n')
    runtime = '''#include <cstdint>
struct CPUContext { uint32_t pc = 0; };
uint32_t observed = 0;
namespace nwii::runtime {
void handle_syscall(CPUContext& ctx) { observed = ctx.pc; }
}
int main() {
  CPUContext ctx{};
''' + ''.join(calls) + '  return 0;\n}\n'
    compile_run(compiler, runtime, False, root / 'dispatch.cpp')
    return 6  # 3 emitted-code checks + 3 native callback observations


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cxx', default='g++', help='C++20 compiler')
    args = p.parse_args()
    passed = 0
    with tempfile.TemporaryDirectory(prefix='v26_sc_pc_') as d:
        root = Path(d)
        file = root / 'nWiiRecomp/src/recompiler.cpp'
        file.parent.mkdir(parents=True)
        untouched = '// untouched preface\n'
        suffix = '  } else { /* untouched fallback */ }\n'
        original = untouched + OLD + suffix
        file.write_text(original, encoding='utf-8')
        ensure(apply(root) == 'installed', 'patch not installed')
        ensure(file.read_text() == untouched + NEW + suffix, 'wrong replacement')
        passed += 2
        ensure(apply(root) == 'already applied', 'patch not idempotent')
        ensure(file.read_text() == untouched + NEW + suffix, 'second patch modified file')
        passed += 2
        for invalid in (
            untouched + suffix,  # no sc branch
            untouched + OLD + OLD + suffix,  # ambiguous duplicates
            untouched + OLD + NEW + suffix,  # partially patched upstream
            untouched + OLD.replace('opcode() == 17', 'opcode() == 18') + suffix,
            untouched + OLD.replace('handle_syscall(ctx)', 'handle_syscall(other)') + suffix,
        ):
            reject_without_writes(root, invalid)
            passed += 1
        passed += test_emitted_cpp(root, args.cxx)
    print(f'PASS: {passed} V26 original-free patch, fail-closed and native syscall-PC checks')


if __name__ == '__main__':
    main()
