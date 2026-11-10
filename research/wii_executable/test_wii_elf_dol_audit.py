"""Original-free synthetic checks for Wii ELF/DOL symbol alignment."""
import struct
import unittest

from wii_elf_dol_audit import inspect_elf, match_dol


def fixture():
    elf = bytearray(0x400)
    elf[:16] = b'\x7fELF\x01\x02\x01' + bytes(9)
    shstr = b'\0.text\0.symtab\0.strtab\0.shstrtab\0'
    names = b'\0example.cpp\0entryfunc\0'
    struct.pack_into('>16sHHIIIIIHHHHHH', elf, 0, bytes(elf[:16]),
                     2, 20, 1, 0x80004000, 0, 0x300, 0x80000000,
                     52, 0, 0, 40, 5, 4)
    text = b'\x4e\x80\x00\x20\x60\x00\x00\x00'  # blr, nop
    elf[0x100:0x108] = text
    elf[0x130:0x130+len(shstr)] = shstr
    elf[0x160:0x160+len(names)] = names
    struct.pack_into('>IIIBBH', elf, 0x210, names.index(b'example.cpp'), 0, 0, 4, 0, 0xfff1)
    struct.pack_into('>IIIBBH', elf, 0x220, names.index(b'entryfunc'), 0x80004000, 8, 2, 0, 1)
    sh = lambda i, *vals: struct.pack_into('>IIIIIIIIII', elf, 0x300 + i*40, *vals)
    sh(1, shstr.index(b'.text'), 1, 6, 0x80004000, 0x100, 8, 0, 0, 4, 0)
    sh(2, shstr.index(b'.symtab'), 2, 0, 0, 0x200, 48, 3, 2, 4, 16)
    sh(3, shstr.index(b'.strtab'), 3, 0, 0, 0x160, len(names), 0, 0, 1, 0)
    sh(4, shstr.index(b'.shstrtab'), 3, 0, 0, 0x130, len(shstr), 0, 0, 1, 0)
    dol = bytearray(0x140)
    struct.pack_into('>I', dol, 0, 0x100)
    struct.pack_into('>I', dol, 18*4, 0x80004000)
    struct.pack_into('>I', dol, 36*4, 32)
    struct.pack_into('>I', dol, 56*4, 0x80004000)
    dol[0x100:0x108] = text
    return bytes(elf), bytes(dol)


class TestWiiELFDolAudit(unittest.TestCase):
    def test_valid_elf(self):
        elf, _ = fixture()
        r, sections = inspect_elf(elf)
        self.assertEqual(r['symbol_entries'], 3)
        self.assertEqual(r['function_symbol_entries'], 1)
        self.assertEqual(r['unique_source_file_names'], 1)
        self.assertEqual(r['function_byte_span_union'], 8)
        self.assertEqual(len(sections), 5)

    def test_dol_exact(self):
        elf, dol = fixture()
        r, sections = inspect_elf(elf)
        result = match_dol(elf, dol, sections, r)
        self.assertEqual(result['nonempty_dol_sections'], 1)
        self.assertEqual(result['total_compared_nonpadding_bytes'], 8)
        self.assertEqual(result['total_zero_padding_bytes'], 24)

    def test_dol_change_detected(self):
        elf, dol = fixture()
        changed = bytearray(dol)
        changed[0x102] ^= 1
        r, sections = inspect_elf(elf)
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            match_dol(elf, bytes(changed), sections, r)

    def test_dol_padding_detected(self):
        elf, dol = fixture()
        changed = bytearray(dol)
        changed[0x110] = 1
        r, sections = inspect_elf(elf)
        with self.assertRaisesRegex(ValueError, 'padding'):
            match_dol(elf, bytes(changed), sections, r)

    def test_wrong_dol_entrypoint(self):
        elf, dol = fixture()
        changed = bytearray(dol)
        struct.pack_into('>I', changed, 56*4, 0x80004004)
        r, sections = inspect_elf(elf)
        with self.assertRaisesRegex(ValueError, 'entrypoints'):
            match_dol(elf, bytes(changed), sections, r)

    def test_bad_elf_machine(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        struct.pack_into('>H', changed, 18, 8)
        with self.assertRaises(ValueError):
            inspect_elf(bytes(changed))

    def test_little_endian_rejected(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        changed[5] = 1
        with self.assertRaises(ValueError):
            inspect_elf(bytes(changed))

    def test_bad_symstr_link(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        struct.pack_into('>I', changed, 0x300 + 2*40 + 24, 1)
        with self.assertRaisesRegex(ValueError, 'string-table link'):
            inspect_elf(bytes(changed))

    def test_function_outside_section_counted(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        struct.pack_into('>I', changed, 0x220 + 4, 0x80014000)
        r, _ = inspect_elf(bytes(changed))
        self.assertEqual(r['sized_in_range_function_entries'], 0)
        self.assertEqual(r['function_symbols_outside_valid_code_ranges'], 1)

    def test_out_of_bounds_section(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        struct.pack_into('>I', changed, 0x300 + 40 + 20, 0xffffffff)
        with self.assertRaises(ValueError):
            inspect_elf(bytes(changed))

    def test_missing_symtab(self):
        elf, _ = fixture()
        changed = bytearray(elf)
        struct.pack_into('>I', changed, 0x300 + 2*40 + 4, 1)
        with self.assertRaisesRegex(ValueError, 'symbol table'):
            inspect_elf(bytes(changed))

    def test_dol_oversized(self):
        elf, dol = fixture()
        changed = bytearray(dol)
        struct.pack_into('>I', changed, 36*4, 0xffffffff)
        r, sections = inspect_elf(elf)
        with self.assertRaises(ValueError):
            match_dol(elf, bytes(changed), sections, r)

    def test_nonbytes_input(self):
        elf, _ = fixture()
        with self.assertRaises(ValueError):
            inspect_elf(bytearray(elf))


if __name__ == '__main__':
    unittest.main()
