#!/usr/bin/env python3
"""Read-only Wii PowerPC ELF symbol and matching DOL section audit.

All results are aggregates. No original functions or retail image bytes are
emitted or saved. A Wii ELF is a code-reference source, not PC source code.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

MAX_IMAGE_BYTES = 64 * 1024 * 1024
MAX_SECTIONS = 256
MAX_SYMS = 1_000_000
SHT_PROGBITS, SHT_SYMTAB, SHT_STRTAB, SHT_NOBITS = 1, 2, 3, 8
SHF_EXECINSTR = 4
STT_FUNC, STT_FILE = 2, 4


def _cstring(blob, offset):
    if offset >= len(blob):
        raise ValueError('String table offset outside bounds')
    end = blob.find(b'\0', offset)
    if end < 0:
        raise ValueError('Unterminated string-table entry')
    try:
        return blob[offset:end].decode('utf-8')
    except UnicodeDecodeError:
        return blob[offset:end].decode('latin-1')


def inspect_elf(blob):
    if type(blob) is not bytes or not 52 <= len(blob) <= MAX_IMAGE_BYTES:
        raise ValueError('ELF must be bounded bytes')
    if blob[:16] != b'\x7fELF\x01\x02\x01' + bytes(9):
        raise ValueError('Expected ELF32 big-endian System-V image')
    (_, etype, machine, version, entry, phoff, shoff, flags, ehsize,
     phentsize, phnum, shentsize, shnum, shstrndx) = struct.unpack_from('>16sHHIIIIIHHHHHH', blob)
    if (etype != 2 or machine != 20 or version != 1 or ehsize != 52 or
            not 3 <= shnum <= MAX_SECTIONS or shentsize != 40 or
            shstrndx == 0 or shstrndx >= shnum or shoff < 52 or
            shoff + 40 * shnum > len(blob)):
        raise ValueError('Unsupported or malformed Wii PowerPC ELF header')
    if phnum and (phentsize != 32 or phoff < 52 or
                  phoff + phentsize * phnum > len(blob)):
        raise ValueError('Malformed ELF program header table')
    sections = []
    for i in range(shnum):
        (nameidx, typ, fl, addr, offset, size, link,
         info, align, entsize) = struct.unpack_from('>IIIIIIIIII', blob, shoff + 40 * i)
        if typ != SHT_NOBITS and (offset > len(blob) or size > len(blob) - offset):
            raise ValueError('Section payload outside file')
        sections.append(dict(nameidx=nameidx, type=typ, flags=fl, address=addr,
                             offset=offset, size=size, link=link, entsize=entsize))
    strsec = sections[shstrndx]
    if strsec['type'] != SHT_STRTAB:
        raise ValueError('Section-name table is not STRTAB')
    st = blob[strsec['offset']:strsec['offset'] + strsec['size']]
    for i, sec in enumerate(sections):
        sec['name'] = '' if i == 0 and sec['nameidx'] == 0 else _cstring(st, sec['nameidx'])
    exec_secs = [(i, sec) for i, sec in enumerate(sections)
                 if sec['type'] == SHT_PROGBITS and sec['flags'] & SHF_EXECINSTR]
    if not exec_secs or not any(s['address'] <= entry < s['address'] + s['size']
                                for _, s in exec_secs):
        raise ValueError('ELF entrypoint outside executable section')
    symsecs = [(i, sec) for i, sec in enumerate(sections) if sec['type'] == SHT_SYMTAB]
    if len(symsecs) != 1:
        raise ValueError('Expected exactly one original symbol table')
    _, syms = symsecs[0]
    if (syms['entsize'] != 16 or syms['size'] % 16 or
            syms['size'] // 16 > MAX_SYMS or syms['link'] >= len(sections)):
        raise ValueError('Invalid symbol table range')
    linked = sections[syms['link']]
    if linked['type'] != SHT_STRTAB:
        raise ValueError('Symbol table has invalid string-table link')
    symbol_names = blob[linked['offset']:linked['offset'] + linked['size']]
    count_type = Counter()
    count_bind = Counter()
    funcs_by_sec = Counter()
    sized_func_count = 0
    func_bytes = 0
    func_intervals = {}
    source_files = set()
    source_file_entries = 0
    out_of_section = 0
    for i in range(syms['size'] // 16):
        (nameidx, address, size, info, other, sec_idx) = struct.unpack_from(
            '>IIIBBH', blob, syms['offset'] + 16 * i)
        typ, bind = info & 15, info >> 4
        count_type[typ] += 1
        count_bind[bind] += 1
        if typ == STT_FILE:
            source_file_entries += 1
            source_files.add(_cstring(symbol_names, nameidx))
        if typ != STT_FUNC:
            continue
        if sec_idx >= len(sections):
            out_of_section += 1
            continue
        sec = sections[sec_idx]
        if not (sec['flags'] & SHF_EXECINSTR) or size == 0 or address < sec['address'] or (
                address - sec['address'] > sec['size'] or
                size > sec['size'] - (address - sec['address'])):
            out_of_section += 1
            continue
        _cstring(symbol_names, nameidx)
        sized_func_count += 1
        func_bytes += size
        funcs_by_sec[sec['name']] += 1
        func_intervals.setdefault(sec_idx, []).append((address, address + size))
    covered = 0
    for intervals in func_intervals.values():
        intervals.sort()
        left, right = intervals[0]
        for a, b in intervals[1:]:
            if a > right:
                covered += right - left
                left, right = a, b
            else:
                right = max(right, b)
        covered += right - left
    return {
        'format': 'wii-elf-symtab-dol-byte-audit-v1',
        'elf_bytes': len(blob),
        'entrypoint': f'0x{entry:08X}',
        'section_count': len(sections),
        'program_header_count': phnum,
        'symbol_entries': syms['size'] // 16,
        'function_symbol_entries': count_type[STT_FUNC],
        'sized_in_range_function_entries': sized_func_count,
        'function_symbols_outside_valid_code_ranges': out_of_section,
        'unique_source_file_names': len(source_files),
        'source_file_symbol_entries': source_file_entries,
        'function_byte_span_sum': func_bytes,
        'function_byte_span_union': covered,
        'executable_section_bytes': sum(s['size'] for _, s in exec_secs),
        'function_counts_by_executable_section': dict(sorted(funcs_by_sec.items())),
        'executable_sections': [dict(name=s['name'], address=f"0x{s['address']:08X}",
                                     size=s['size']) for _, s in exec_secs],
        'relocation_entries': sum(s['size'] // s['entsize'] for s in sections
                                  if s['type'] in (4, 9) and s['entsize'] > 0),
        'interpretation': ('Named, sized symbols in authentic PowerPC ELF, '
                           'not original source code or a PS2-to-Wii function match')
    }, sections


def match_dol(elf, dol, elf_sections, elf_report):
    if type(dol) is not bytes or not 0x100 <= len(dol) <= MAX_IMAGE_BYTES:
        raise ValueError('DOL must be bounded bytes')
    fields = struct.unpack_from('>57I', dol)
    if fields[56] != int(elf_report['entrypoint'], 16):
        raise ValueError('DOL and ELF entrypoints disagree')
    used_files = []
    matched = []
    sections = [s for s in elf_sections if s['type'] == SHT_PROGBITS and s['flags'] & 2]
    for i in range(18):
        off, addr, length = fields[i], fields[18+i], fields[36+i]
        if (off, addr, length) == (0, 0, 0):
            continue
        if not all((off, addr, length)) or off < 0x100 or off > len(dol) or length > len(dol) - off:
            raise ValueError('Malformed DOL section span')
        if any(off < hi and lo < off + length for lo, hi in used_files):
            raise ValueError('Overlapping DOL file spans')
        used_files.append((off, off + length))
        targets = [s for s in sections if s['address'] == addr and
                   s['size'] <= length and length - s['size'] < 32 and
                   (s['flags'] & SHF_EXECINSTR) == (SHF_EXECINSTR if i < 7 else 0)]
        if len(targets) != 1:
            raise ValueError('DOL section does not map uniquely to ELF section')
        s = targets[0]
        if dol[off:off+s['size']] != elf[s['offset']:s['offset']+s['size']]:
            raise ValueError('DOL and ELF bytes differ')
        if any(dol[off+s['size']:off+length]):
            raise ValueError('DOL section padding is not zero')
        matched.append((i, s['name'], s['size'], length - s['size']))
    bss_start, bss_size = fields[54:56]
    bss = [s for s in elf_sections if s['type'] == SHT_NOBITS and s['flags'] & 2]
    if bss and (not bss_start or not bss_size or any(
            s['address'] < bss_start or s['size'] > bss_start + bss_size - s['address']
            for s in bss)):
        raise ValueError('ELF NOBITS section outside DOL BSS range')
    if not matched:
        raise ValueError('DOL maps no ELF sections')
    return {'dol_bytes': len(dol), 'entrypoint_equal': True,
            'nonempty_dol_sections': len(matched),
            'text_sections_identical': sum(i < 7 for i, _, _, _ in matched),
            'data_sections_identical': sum(i >= 7 for i, _, _, _ in matched),
            'total_compared_nonpadding_bytes': sum(size for _, _, size, _ in matched),
            'total_zero_padding_bytes': sum(pad for _, _, _, pad in matched),
            'all_compared_bytes_identical': True,
            'all_section_padding_zero': True,
            'elf_bss_sections_within_dol_bss': len(bss),
            'mapping': [{'dol_index': i, 'elf_section': name, 'bytes': size, 'zero_pad': pad}
                        for i, name, size, pad in matched]}


def _load(path):
    path = path.absolute()
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError('Unsafe, missing or oversized owner-local input')
    before = path.stat()
    b = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input changed while reading')
    return b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wii-elf', required=True, type=Path)
    parser.add_argument('--wii-dol', type=Path)
    args = parser.parse_args()
    elf = _load(args.wii_elf)
    report, sections = inspect_elf(elf)
    if args.wii_dol is not None:
        report['dol_match'] = match_dol(elf, _load(args.wii_dol), sections, report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
