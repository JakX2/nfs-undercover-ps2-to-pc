"""Original-free PPC branch and named function call-graph checks."""
import struct
import unittest

from test_wii_elf_dol_audit import fixture
from wii_ppc_call_graph import analyze, branch_kind, signed_field


def code_image(*words, local_function=False):
    elf, _ = fixture()
    source = bytearray(elf)
    assert len(words) <= 12
    for i, word in enumerate(words):
        struct.pack_into('>I', source, 0x100 + 4 * i, word)
    struct.pack_into('>I', source, 0x300 + 40 + 20, 4 * len(words))  # .text size
    struct.pack_into('>I', source, 0x220 + 8, 4 * len(words))  # symbol size
    if local_function:
        struct.pack_into('>I', source, 0x300 + 2 * 40 + 28, 3)  # symtab.sh_info
        source[0x220 + 12] = 0x02  # STB_LOCAL, STT_FUNC
    return bytes(source)


class TestPpcBranch(unittest.TestCase):
    def test_positive_relative_bl(self):
        self.assertEqual(branch_kind(0x48000009, 0x80004000),
                         ('direct_call', 0x80004008))

    def test_negative_relative_bl(self):
        self.assertEqual(branch_kind(0x4BFFFFFD, 0x80004004),
                         ('direct_call', 0x80004000))

    def test_absolute_branch(self):
        self.assertEqual(branch_kind(0x48000103, 0x80004000),
                         ('direct_call', 0x100))

    def test_relative_wrap(self):
        self.assertEqual(branch_kind(0x48000009, 0xFFFFFFFC),
                         ('direct_call', 4))

    def test_link_bit_separates_jump(self):
        self.assertEqual(branch_kind(0x48000008, 0x80004000),
                         ('direct_jump', 0x80004008))

    def test_conditional_link(self):
        self.assertEqual(branch_kind(0x40000009, 0x80004000),
                         ('conditional_call', 0x80004008))

    def test_conditional_negative(self):
        self.assertEqual(branch_kind(0x40FFFFFD, 0x80004004),
                         ('conditional_call', 0x80004000))

    def test_bctrl(self):
        self.assertEqual(branch_kind(0x4E800421, 0x80004000),
                         ('indirect_call', None))

    def test_blrl(self):
        self.assertEqual(branch_kind(0x4E800021, 0x80004000),
                         ('indirect_call', None))

    def test_blr_not_call(self):
        self.assertEqual(branch_kind(0x4E800020, 0x80004000),
                         ('indirect_jump', None))

    def test_nonbranch(self):
        self.assertIsNone(branch_kind(0x60000000, 0x80004000))

    def test_sign_extension(self):
        self.assertEqual(signed_field(0x03FFFFFC, 26), -4)
        self.assertEqual(signed_field(0x0000FFFC, 16), -4)


class TestSourceFreeCallGraph(unittest.TestCase):
    def test_interior_and_indirect(self):
        data = code_image(0x48000005, 0x4E800421, 0x60000000)
        r = analyze(data)
        self.assertEqual(r['named_scanned_functions'], 1)
        self.assertEqual(r['static_direct_branch_with_link_sites'], 1)
        self.assertEqual(r['direct_call_sites_resolving_inside_named_functions'], 1)
        self.assertEqual(r['resolved_to_function_interior_sites'], 1)
        self.assertEqual(r['self_call_sites'], 1)
        self.assertEqual(r['unresolved_register_branch_with_link_sites'], 1)
        self.assertEqual(r['global_or_weak_function_symbols_without_compilation_unit'], 1)
        self.assertEqual(r['compilation_units_with_local_functions'], 0)

    def test_local_file_assignment(self):
        data = code_image(0x48000005, 0x4E800020, local_function=True)
        r = analyze(data)
        self.assertEqual(r['local_function_symbols_with_supported_compilation_unit'], 1)
        self.assertEqual(r['compilation_units_with_local_functions'], 1)
        self.assertEqual(r['same_compilation_unit_call_sites'], 1)
        self.assertEqual(r['calls_with_unassignable_compilation_unit'], 0)

    def test_jump_not_call(self):
        data = code_image(0x48000004, 0x4E800020)
        r = analyze(data)
        self.assertEqual(r['static_direct_branch_with_link_sites'], 0)
        self.assertEqual(r['ordinary_unconditional_branch_sites_not_classed_as_calls'], 1)

    def test_external_call(self):
        data = code_image(0x48000041, 0x4E800020)
        r = analyze(data)
        self.assertEqual(r['direct_call_sites_not_resolving_inside_named_functions'], 1)

    def test_invalid_symtab_boundary(self):
        data = bytearray(code_image(0x60000000))
        struct.pack_into('>I', data, 0x300 + 2 * 40 + 28, 100)
        with self.assertRaisesRegex(ValueError, 'local/global'):
            analyze(bytes(data))

    def test_local_file_marker_beyond_boundary(self):
        data = bytearray(code_image(0x60000000))
        struct.pack_into('>I', data, 0x300 + 2 * 40 + 28, 1)
        with self.assertRaisesRegex(ValueError, 'File symbol'):
            analyze(bytes(data))

    def test_symbol_overlap_rejected(self):
        data = bytearray(code_image(0x60000000, 0x60000000))
        struct.pack_into('>I', data, 0x300 + 2*40 + 20, 64)
        struct.pack_into('>IIIBBH', data, 0x230, 1, 0x80004004, 4, 0x12, 0, 1)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            analyze(bytes(data))

    def test_bad_function_alignment_rejected(self):
        data = bytearray(code_image(0x60000000, 0x60000000))
        struct.pack_into('>I', data, 0x220 + 8, 7)
        with self.assertRaisesRegex(ValueError, 'Unaligned'):
            analyze(bytes(data))

    def test_bad_function_name_raises(self):
        data = bytearray(code_image(0x60000000))
        struct.pack_into('>I', data, 0x220, 0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError, 'bounds'):
            analyze(bytes(data))


class TestFocusedGraph(unittest.TestCase):
    def test_focus_one_function(self):
        r = analyze(code_image(0x48000005, 0x4E800421), 'entryfunc')
        focus = r['focus']
        self.assertEqual(focus['function_address'], '0x80004000')
        self.assertEqual(focus['named_direct_callers_count'], 1)
        self.assertEqual(focus['named_direct_callees_count'], 1)
        self.assertEqual(focus['incoming_direct_call_sites'], 1)
        self.assertEqual(focus['outgoing_direct_call_sites'], 1)
        self.assertEqual(focus['outgoing_indirect_branch_with_link_sites'], 1)
        self.assertEqual(focus['top_callees'][0]['function_symbol'], 'entryfunc')

    def test_unknown_focus_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            analyze(code_image(0x60000000), 'missing')

    def test_empty_focus_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            analyze(code_image(0x60000000), '')
