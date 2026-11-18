"""Synthetic-only tests, no copyrighted game data needed."""
import struct
import unittest

from object_reference_map import inspect_record, audit_records, pointer_groups


def chunk(tag, size):
    assert size % 16 == 0
    return tag + struct.pack('<I', size) + b'\0' * (size - 8)


def nrtp_rows(a=((32, 0x10003, 8), (40, 0x10003, 44)),
              b=((112, 0x10003, 8), (144, 0x10003, 44))):
    rows = [(0, 0x10002, 0), *a, (0, 2, 0), *b, (0, 0, 0)]
    body = b''.join(struct.pack('<3I', *t) for t in rows)
    result = b'NrtP' + struct.pack('<I', 0) + body
    result += b'\0' * (-len(result) % 16)
    return result[:4] + struct.pack('<I', len(result)) + result[8:]


def fixture():
    pool = b'alpha\0beta\0'
    pool += b'\0' * (-len(pool) % 8)
    pool = b'ErtS' + struct.pack('<I', 8 + len(pool)) + pool
    assert len(pool) == 24
    text = pool + b'\0' * 40
    prefix = (chunk(b'sreV', 16), chunk(b'NpeD', 64), chunk(b'NrtS', 16))
    data = chunk(b'NtaD', 80)
    entries = [(0x8E112EB7, 32, 104, 0x11223344),
               (0x8E112EB7, 32, 136, 0)]
    exports = b'NpxE' + struct.pack('<III', 48, 2, 0)
    exports += b''.join(struct.pack('<4I', *entry) for entry in entries)
    assert len(exports) == 48
    return {'text': text, 'chunks': dict(zip(
        ('sreV', 'NpeD', 'NrtS', 'NtaD', 'NpxE', 'NrtP'),
        (*prefix, data, exports, nrtp_rows())))}


class ObjectReferenceMapTests(unittest.TestCase):
    def test_valid(self):
        result = inspect_record(fixture())
        self.assertEqual((result['objects'], result['group_a'], result['group_b']), (2, 2, 2))
        self.assertEqual(result['objects_with_group_b_references'], 2)
        self.assertEqual(result['terminal_nonempty_objects'], 1)
        self.assertEqual(result['group_a_post_string_self_next'], 1)
        self.assertEqual(result['object_padding_bytes'], 8)

    def test_aggregate(self):
        result = audit_records([fixture(), fixture()])
        self.assertEqual((result['records'], result['objects'], result['group_b']), (2, 4, 4))

    def test_bad_first_offset(self):
        rec = fixture()
        data = bytearray(rec['chunks']['NpxE'])
        struct.pack_into('<I', data, 16 + 8, 112)
        rec['chunks']['NpxE'] = bytes(data)
        with self.assertRaises(ValueError):
            inspect_record(rec)

    def test_zero_length_terminal_is_bad(self):
        rec = fixture()
        data = bytearray(rec['chunks']['NpxE'])
        struct.pack_into('<I', data, 16 + 16 + 4, 0)
        rec['chunks']['NpxE'] = bytes(data)
        with self.assertRaisesRegex(ValueError, 'signature or alignment'):
            inspect_record(rec)

    def test_nonzero_aux_pointer_slot(self):
        rec = fixture()
        data = bytearray(rec['chunks']['NtaD'])
        data[112-96] = 1
        rec['chunks']['NtaD'] = bytes(data)
        with self.assertRaisesRegex(ValueError, 'Group B source site'):
            inspect_record(rec)

    def test_nonzero_text_pointer_slot(self):
        rec = fixture()
        rec['text'] = rec['text'][:32] + b'X' + rec['text'][33:]
        with self.assertRaisesRegex(ValueError, 'Group A pointer site'):
            inspect_record(rec)

    def test_b_source_in_trailing_padding(self):
        rec = fixture()
        rec['chunks']['NrtP'] = nrtp_rows(b=((168, 0x10003, 8), (144, 0x10003, 44)))
        with self.assertRaisesRegex(ValueError, 'does not belong'):
            inspect_record(rec)

    def test_bad_chain(self):
        rec = fixture()
        data = bytearray(rec['chunks']['NpxE'])
        struct.pack_into('<I', data, 16 + 16 + 8, 144)
        rec['chunks']['NpxE'] = bytes(data)
        with self.assertRaisesRegex(ValueError, 'chain'):
            inspect_record(rec)

    def test_nonzero_gap_between_objects(self):
        rec = fixture()
        entries = bytearray(rec['chunks']['NpxE'])
        struct.pack_into('<I', entries, 20, 28)
        rec['chunks']['NpxE'] = bytes(entries)
        data = bytearray(rec['chunks']['NtaD'])
        data[132-96] = 77
        rec['chunks']['NtaD'] = bytes(data)
        with self.assertRaisesRegex(ValueError, 'inter-object padding'):
            inspect_record(rec)

    def test_nonzero_tail(self):
        rec = fixture()
        data = bytearray(rec['chunks']['NtaD'])
        data[-1] = 1
        rec['chunks']['NtaD'] = bytes(data)
        with self.assertRaisesRegex(ValueError, 'trailing padding'):
            inspect_record(rec)

    def test_misplaced_terminal_marker(self):
        rec = fixture()
        entries = bytearray(rec['chunks']['NpxE'])
        struct.pack_into('<I', entries, 16 + 12, 0)
        rec['chunks']['NpxE'] = bytes(entries)
        with self.assertRaisesRegex(ValueError, 'terminal marker'):
            inspect_record(rec)

    def test_duplicate_B_slot(self):
        rec = fixture()
        rec['chunks']['NrtP'] = nrtp_rows(b=((112, 0x10003, 8), (112, 0x10003, 44)))
        with self.assertRaisesRegex(ValueError, 'Repeated group B'):
            inspect_record(rec)

    def test_wrong_A_post_ErtS_relation(self):
        rec = fixture()
        rec['chunks']['NrtP'] = nrtp_rows(a=((32, 0x10003, 8), (40, 0x10003, 48)))
        with self.assertRaisesRegex(ValueError, 'Unsupported group A'):
            inspect_record(rec)

    def test_bad_NrtP_group_marker(self):
        rec = fixture()
        ptr = bytearray(rec['chunks']['NrtP'])
        struct.pack_into('<I', ptr, 8 + 3 * 12 + 4, 3)
        rec['chunks']['NrtP'] = bytes(ptr)
        with self.assertRaisesRegex(ValueError, 'group B marker'):
            inspect_record(rec)

    def test_outside_text_destination(self):
        rec = fixture()
        rec['chunks']['NrtP'] = nrtp_rows(b=((112, 0x10003, 9999), (144, 0x10003, 44)))
        with self.assertRaisesRegex(ValueError, 'Group B source site'):
            inspect_record(rec)

    def test_no_group_B_reference_in_one_object(self):
        rec = fixture()
        rec['chunks']['NrtP'] = nrtp_rows(b=((112, 0x10003, 8),))
        with self.assertRaisesRegex(ValueError, 'no group B references'):
            inspect_record(rec)


if __name__ == '__main__':
    unittest.main()
