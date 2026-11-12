"""Synthetic-only tests; no original game executable is required."""
from pathlib import Path
import struct
import tempfile
import unittest

from wii_recomp_preflight import PreflightError, emit, parse_elf, parse_dol, verify_elf_dol, find_sda_bases


def make_pair():
    def insn(op, rt, ra, imm):
        return ((op << 26) | (rt << 21) | (ra << 16) | imm).to_bytes(4, "big")

    code = (insn(15, 2, 0, 0x8071) + insn(24, 2, 2, 0x5EE0)
            + insn(15, 13, 0, 0x8070) + insn(24, 13, 13, 0xE8E0)
            + b"\x4E\x80\x00\x20" + b"\x00" * 4
            + b"\x4E\x80\x00\x20" + b"\x00" * 4)
    assert len(code) == 32
    elf = bytearray(b"\x00" * 0x100)
    elf[0:16] = b"\x7fELF\x01\x02\x01" + b"\x00" * 9
    sections = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
    init_offset = len(elf)
    elf.extend(code)
    symtab = b"\x00" * 16 + struct.pack(">IIIBBH", 1, 0x80004000, 20, 0x12, 0, 1) + struct.pack(">IIIBBH", 18, 0x80004018, 4, 0x12, 0, 1)
    sym_offset = len(elf)
    elf.extend(symtab)
    strings = b"\0__init_registers\0main\0"
    str_offset = len(elf)
    elf.extend(strings)
    names = b"\0.init\0.symtab\0.strtab\0.shstrtab\0"
    shstr_offset = len(elf)
    elf.extend(names)
    while len(elf) % 4:
        elf.append(0)
    shoff = len(elf)
    sections.extend([
        (1, 1, 6, 0x80004000, init_offset, len(code), 0, 0, 4, 0),
        (7, 2, 0, 0, sym_offset, len(symtab), 3, 1, 4, 16),
        (15, 3, 0, 0, str_offset, len(strings), 0, 0, 1, 0),
        (23, 3, 0, 0, shstr_offset, len(names), 0, 0, 1, 0),
    ])
    for sec in sections:
        elf.extend(struct.pack(">10I", *sec))
    struct.pack_into(">HHIIIIIHHHHHH", elf, 16, 2, 20, 1, 0x80004000, 0, shoff, 0x80000000, 52, 32, 0, 40, len(sections), 4)

    dol = bytearray(b"\x00" * 0x100)
    struct.pack_into(">I", dol, 0, 0x100)
    struct.pack_into(">I", dol, 0x48, 0x80004000)
    struct.pack_into(">I", dol, 0x90, len(code))
    struct.pack_into(">I", dol, 0xE0, 0x80004000)
    dol.extend(code)
    return bytes(elf), bytes(dol)


class WiiRecompPreflightTests(unittest.TestCase):
    def test_generated_map_and_manifest(self):
        elf, dol = make_pair()
        with tempfile.TemporaryDirectory() as d:
            out = emit(elf, dol, Path(d))
            self.assertEqual(out["elf_function_symbols"], 2)
            self.assertEqual(out["unique_function_addresses"], 2)
            self.assertEqual(out["dol_nonpadding_bytes_verified"], 32)
            self.assertEqual(out["r2_sda2_base"], "0x80715EE0")
            self.assertEqual(out["r13_sda_base"], "0x8070E8E0")
            self.assertIn("allow_unsupported_instructions: false", Path(d, "undercover-wii-generic.yml").read_text())
            self.assertEqual(len(Path(d, "private_function_map.txt").read_text().splitlines()), 2)

    def test_bad_dol_payload(self):
        elf, dol = make_pair()
        corruption = bytearray(dol)
        corruption[-1] = 0xFF
        with self.assertRaisesRegex(PreflightError, "ELF/DOL bytes differ"):
            verify_elf_dol(parse_elf(elf), parse_dol(corruption))

    def test_bad_entry(self):
        elf, dol = make_pair()
        corruption = bytearray(dol)
        struct.pack_into(">I", corruption, 0xE0, 0x80004004)
        with self.assertRaisesRegex(PreflightError, "entrypoint disagreement"):
            verify_elf_dol(parse_elf(elf), parse_dol(corruption))

    def test_malformed_section_table(self):
        elf, _ = make_pair()
        with self.assertRaises(PreflightError):
            parse_elf(elf[:100])

    def test_missing_sda_init(self):
        elf, _ = make_pair()
        corrupt = bytearray(elf)
        corrupt[0x100:0x104] = b"\x00" * 4
        with self.assertRaisesRegex(PreflightError, "both r2 and r13"):
            find_sda_bases(parse_elf(corrupt))


if __name__ == "__main__":
    unittest.main()
