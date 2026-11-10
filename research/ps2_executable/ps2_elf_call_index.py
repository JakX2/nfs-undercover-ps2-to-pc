#!/usr/bin/env python3
"""Read-only, bounded PS2 MIPS ELF direct-control-transfer candidate index.

A linear instruction-word scan is NOT a disassembly or validated call graph.
Embedded data, jump tables, unreachable blocks and EE instructions can cause
false positives. VU microcode is deliberately excluded from MIPS scanning.
"""
import argparse
import json
from pathlib import Path
import struct

MAX_FILE = 64 * 1024 * 1024
MAX_SECTIONS = 128
CODE_SECTIONS = ('.text', '.over')


def inspect(blob):
    if type(blob) is not bytes or not 52 <= len(blob) <= MAX_FILE:
        raise ValueError('ELF input must be bounded bytes')
    if blob[:16] != b'\x7fELF\x01\x01\x01' + bytes(9):
        raise ValueError('Expected ELF32 little-endian System-V ELF')
    (etype, machine, version, entry, phoff, shoff, flags, ehsize,
     phentsize, phnum, shentsize, shnum, shstrndx) = struct.unpack_from('<HHIIIIIHHHHHH', blob, 16)
    if (etype != 2 or machine != 8 or version != 1 or ehsize != 52 or
            shentsize != 40 or not 2 <= shnum <= MAX_SECTIONS or
            shstrndx == 0 or shstrndx >= shnum or
            shoff < 52 or shoff + shnum * 40 > len(blob)):
        raise ValueError('Unsupported or malformed MIPS ELF header')
    if phnum and (phentsize != 32 or phoff < 52 or
                  phoff + phnum * phentsize > len(blob)):
        raise ValueError('Malformed program header table')
    records = []
    for n in range(shnum):
        name, typ, shflags, address, offset, size, link, info, align, entsize = struct.unpack_from(
            '<IIIIIIIIII', blob, shoff + n * 40)
        if typ != 8 and (offset > len(blob) or size > len(blob) - offset):
            raise ValueError('Section exceeds ELF file bounds')
        records.append((name, typ, shflags, address, offset, size))
    _, strtype, _, _, stroff, strlen = records[shstrndx]
    if strtype != 3 or not strlen:
        raise ValueError('Missing section-name string table')
    names = blob[stroff:stroff + strlen]

    def read_name(index):
        if index >= len(names):
            raise ValueError('Invalid section name index')
        end = names.find(b'\0', index)
        if end < 0:
            raise ValueError('Unterminated section name')
        try:
            return names[index:end].decode('ascii')
        except UnicodeDecodeError:
            raise ValueError('Non-ASCII section name') from None

    sections = {}
    for rec in records[1:]:
        name, typ, shflags, addr, off, size = rec
        key = read_name(name)
        if key in sections:
            raise ValueError('Duplicate section name')
        sections[key] = (typ, shflags, addr, off, size)
    if '.text' not in sections:
        raise ValueError('No MIPS .text section')

    code = []
    for name in CODE_SECTIONS:
        if name not in sections:
            continue
        typ, shflags, addr, off, size = sections[name]
        if typ != 1 or not (shflags & 4) or addr % 4 or size % 4 or size == 0:
            raise ValueError('Invalid MIPS code section')
        code.append((name, addr, off, size))
    code_sorted = sorted(code, key=lambda x: x[1])
    if any(a[1] + a[3] > b[1] for a, b in zip(code_sorted, code_sorted[1:])):
        raise ValueError('Overlapping executable address ranges')
    text = sections['.text']
    if not text[2] <= entry < text[2] + text[4] or entry % 4:
        raise ValueError('Entrypoint is outside aligned MIPS .text')
    if '.vutext' in sections:
        typ, shflags, addr, off, size = sections['.vutext']
        if typ != 1 or not (shflags & 4):
            raise ValueError('Invalid VU text section')

    in_code = lambda target: any(a <= target < a + length for _, a, _, length in code)
    result = {'format': 'ps2-elf-mips-call-index-v1', 'entrypoint': f'0x{entry:08X}',
              'mips_header_flags': f'0x{flags:08X}', 'input_size': len(blob),
              'vu_section_bytes_excluded': sections.get('.vutext', (0, 0, 0, 0, 0))[4],
              'sections': [], 'direct_jal_sites': 0, 'direct_jal_in_code': 0,
              'direct_jal_outside_code': 0, 'direct_jal_unique_in_code_targets': 0,
              'unresolved_jalr_sites': 0, 'unconditional_j_sites': 0,
              'entry_window_direct_calls': []}
    all_target_sites = set()
    entry_window_calls = set()
    for name, addr, off, size in code:
        stats = {'name': name, 'address': f'0x{addr:08X}', 'bytes': size,
                 'jal_sites': 0, 'jal_inside_code': 0, 'jalr_sites': 0, 'j_sites': 0}
        for pos in range(0, size, 4):
            pc = addr + pos
            (word,) = struct.unpack_from('<I', blob, off + pos)
            op = word >> 26
            if op == 3:  # JAL immediate (MIPS encoding, direct call candidate)
                target = ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
                stats['jal_sites'] += 1
                result['direct_jal_sites'] += 1
                if in_code(target):
                    stats['jal_inside_code'] += 1
                    result['direct_jal_in_code'] += 1
                    all_target_sites.add(target)
                else:
                    result['direct_jal_outside_code'] += 1
                if entry <= pc < entry + 0x200:
                    entry_window_calls.add(target)
            elif op == 2:  # J direct jump, not necessarily a function call
                stats['j_sites'] += 1
                result['unconditional_j_sites'] += 1
            elif op == 0 and (word & 0x3F) == 9:  # JALR indirect call
                stats['jalr_sites'] += 1
                result['unresolved_jalr_sites'] += 1
        result['sections'].append(stats)
    result['direct_jal_unique_in_code_targets'] = len(all_target_sites)
    result['entry_window_direct_calls'] = [f'0x{x:08X}' for x in sorted(entry_window_calls)]
    result['interpretation'] = ('Linear opcode matches only; not proven instructions, '
                                'function boundaries or runtime call graph')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf', type=Path, help='Owner-local original PS2 executable')
    args = p.parse_args()
    path = args.elf.absolute()
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE:
        p.error('Refusing missing, symlinked or oversized file')
    before = path.stat()
    report = inspect(path.read_bytes())
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        p.error('Source file changed during read')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
