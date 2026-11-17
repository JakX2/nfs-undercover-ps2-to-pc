#!/usr/bin/env python3
"""Independent mock ELF32 regression tests; no Undercover executable content."""
from __future__ import annotations
from pathlib import Path
import struct
import unittest

from make_private_elf_symbol_map import HEADER, SECTION, SYMBOL, ENTRY, parse_functions, csv_lines


def make_mock_elf(*, machine=20, duplicate=False, truncated=False):
    sym_offset = 0x100
    funcs = [(0,0,0,0,0,0), (1,ENTRY,8,2,0,1), (2,0x80004050,12,2,0,1),
             (3,0x80004070,20,1,0,1)]
    if duplicate:
        funcs.append((4,ENTRY,12,2,0,1))
    symdata = b"".join(SYMBOL.pack(*s) for s in funcs)
    shoff = sym_offset + len(symdata)
    ident = b"\x7fELF\x01\x02\x01" + b"\x00" * 9
    header = HEADER.pack(ident,2,machine,1,ENTRY,0,shoff,0,HEADER.size,0,0,SECTION.size,2,0)
    section = SECTION.pack(0,2,0,0,sym_offset,len(symdata),0,0,4,SYMBOL.size)
    content = header.ljust(sym_offset,b"\0") + symdata + SECTION.pack(*([0]*10)) + section
    return content[:-4] if truncated else content


class ElfFunctionMapTests(unittest.TestCase):
    def test_read_original_free_functions_and_skip_data(self):
        funcs = parse_functions(make_mock_elf())
        self.assertEqual(funcs,{ENTRY:8,0x80004050:12})
        self.assertEqual(csv_lines(funcs).splitlines()[0],"Name,Location,Size")
        self.assertIn("fn_8000403C,8000403C,8",csv_lines(funcs))

    def test_duplicate_chooses_largest_span(self):
        self.assertEqual(parse_functions(make_mock_elf(duplicate=True))[ENTRY],12)

    def test_invalid_machine_rejected(self):
        with self.assertRaisesRegex(ValueError,"PowerPC"):
            parse_functions(make_mock_elf(machine=3))

    def test_invalid_section_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError,"sections"):
            parse_functions(make_mock_elf(truncated=True))

    def test_little_endian_rejected(self):
        raw=bytearray(make_mock_elf());raw[5]=1
        with self.assertRaisesRegex(ValueError,"PowerPC"):
            parse_functions(bytes(raw))

    def test_no_missing_or_empty_output(self):
        with self.assertRaises(ValueError):
            csv_lines({})

    def test_missing_start_rejected(self):
        raw=bytearray(make_mock_elf())
        # A synthetic STT_FUNC startup has an 8-byte guest address, mutate it.
        raw[0x100+SYMBOL.size+4:0x100+SYMBOL.size+8] = struct.pack(">I",0x80004044)
        with self.assertRaisesRegex(ValueError,"startup"):
            parse_functions(bytes(raw))


if __name__ == "__main__":
    unittest.main()
