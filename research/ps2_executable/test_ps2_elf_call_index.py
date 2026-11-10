"""Synthetic-only tests for the bounded PS2 ELF call-pattern scanner."""
import struct
import unittest

from ps2_elf_call_index import inspect


def fixture(text_words=(0x0C040008, 0x00000009), vu=False):
    """Minimal no-proprietary-data ELF32/MIPS image."""
    words = list(text_words)
    sections = ['', '.text', '.shstrtab'] + (['.vutext'] if vu else [])
    strings = b'\0'
    idx = {}
    for name in sections[1:]:
        idx[name] = len(strings)
        strings += name.encode('ascii') + b'\0'
    text = b''.join(struct.pack('<I', w) for w in words)
    result = bytearray(0x400)
    result[:16] = b'\x7fELF\x01\x01\x01' + bytes(9)
    shoff = 0x200
    struct.pack_into('<HHIIIIIHHHHHH', result, 16, 2, 8, 1,
                     0x100000, 0, shoff, 0, 52, 0, 0, 40, len(sections), 2)
    result[0x100:0x100 + len(text)] = text
    result[0x180:0x180 + len(strings)] = strings
    struct.pack_into('<IIIIIIIIII', result, shoff + 40, idx['.text'], 1, 6,
                     0x100000, 0x100, len(text), 0, 0, 4, 0)
    struct.pack_into('<IIIIIIIIII', result, shoff + 80, idx['.shstrtab'], 3,
                     0, 0, 0x180, len(strings), 0, 0, 1, 0)
    if vu:
        struct.pack_into('<IIIIIIIIII', result, shoff + 120, idx['.vutext'],
                         1, 6, 0x200000, 0x190, 8, 0, 0, 8, 0)
    return bytes(result)


class TestMipsIndex(unittest.TestCase):
    def test_valid(self):
        r = inspect(fixture((0x0C040001, 0x00000009, 0x08040000)))
        self.assertEqual(r['direct_jal_sites'], 1)
        self.assertEqual(r['direct_jal_in_code'], 1)
        self.assertEqual(r['direct_jal_unique_in_code_targets'], 1)
        self.assertEqual(r['unresolved_jalr_sites'], 1)
        self.assertEqual(r['unconditional_j_sites'], 1)

    def test_vu_excluded(self):
        r = inspect(fixture((0x0C040001,), vu=True))
        self.assertEqual(r['vu_section_bytes_excluded'], 8)

    def test_invalid_magic(self):
        with self.assertRaises(ValueError):
            inspect(b'Z' + fixture()[1:])

    def test_truncated(self):
        with self.assertRaises(ValueError):
            inspect(fixture()[:70])

    def test_nonbytes(self):
        with self.assertRaises(ValueError):
            inspect(bytearray(fixture()))

    def test_entry_outside_text(self):
        b = bytearray(fixture())
        struct.pack_into('<I', b, 24, 0x200000)
        with self.assertRaises(ValueError):
            inspect(bytes(b))

    def test_bad_shstr_index(self):
        b = bytearray(fixture())
        struct.pack_into('<H', b, 50, 99)
        with self.assertRaises(ValueError):
            inspect(bytes(b))

    def test_bad_section_size(self):
        b = bytearray(fixture())
        struct.pack_into('<I', b, 0x200 + 40 + 20, 0xFFFFFFFF)
        with self.assertRaises(ValueError):
            inspect(bytes(b))

    def test_bad_section_name(self):
        b = bytearray(fixture())
        struct.pack_into('<I', b, 0x200 + 40, 999)
        with self.assertRaises(ValueError):
            inspect(bytes(b))

    def test_wrong_machine(self):
        b = bytearray(fixture())
        struct.pack_into('<H', b, 18, 3)
        with self.assertRaises(ValueError):
            inspect(bytes(b))


if __name__ == '__main__':
    unittest.main()
