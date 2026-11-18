"""Synthetic-only regression tests for stable candidate IDs and reference signatures."""
import json
import struct
import unittest

from shared_object_probe import compare, project_record, resource_name
from test_object_reference_map import fixture


def npe(base='gpcore'):
    a = base.encode('ascii') + b'.vlt\0'
    b = base.encode('ascii') + b'.bin\0'
    assert len(a) == len(b)
    data = b'NpeD' + struct.pack('<6I', 0, 2, 10, 20, 0, len(a)) + a + b
    data += b'\0' * (-len(data) % 16)
    return data[:4] + struct.pack('<I', len(data)) + data[8:]


class SharedObjectProbeTests(unittest.TestCase):
    def test_resource_key(self):
        self.assertEqual(resource_name(npe('race_bin_challenge')), 'race_bin_challenge')

    def test_bad_resource_header(self):
        with self.assertRaisesRegex(ValueError, 'NpeD header'):
            resource_name(b'xxxx' + npe()[4:])

    def test_bad_resource_name(self):
        b = bytearray(npe())
        ix = b.index(b'.bin\0')
        b[ix-2] = ord('Q')
        with self.assertRaisesRegex(ValueError, 'Mismatched'):
            resource_name(bytes(b))

    def test_nonzero_resource_padding(self):
        b = bytearray(npe())
        b[-1] = 1
        with self.assertRaisesRegex(ValueError, 'padding'):
            resource_name(bytes(b))

    def test_projection_excludes_zero_marked_entry_from_matching(self):
        result = project_record(fixture())
        self.assertEqual(result['count'], 2)
        self.assertEqual(len(result['by_id']), 1)
        self.assertEqual(sum(result['payload_hash_multiset'].values()), 2)

    def test_projection_named_target_content(self):
        result = project_record(fixture())
        one = result['by_id'][0x11223344]
        self.assertEqual(one[3], ((8, b'alpha'),))
        self.assertEqual(one[4], ())

    def test_compare_same_resource(self):
        projected = project_record(fixture())
        r = compare(projected, projected)
        self.assertEqual(r['shared_nonzero_word3'], 1)
        self.assertEqual(r['identical_payload_when_word3_shared'], 1)
        self.assertEqual(r['same_reference_layout_when_word3_shared'], 1)
        self.assertEqual(r['identical_payload_multiset_count_ignoring_word3'], 2)

    def test_compare_marker_changed_but_payload_unchanged(self):
        one = project_record(fixture())
        two = project_record(fixture())
        original = two['by_id'].pop(0x11223344)
        two['by_id'][0x99999999] = original
        r = compare(one, two)
        self.assertEqual(r['shared_nonzero_word3'], 0)
        self.assertEqual(r['identical_payload_multiset_count_ignoring_word3'], 2)

    def test_changed_payload_but_same_id(self):
        one = project_record(fixture())
        two = project_record(fixture())
        b = list(two['by_id'][0x11223344])
        b[1] = b'X' * 32
        two['by_id'][0x11223344] = tuple(b)
        r = compare(one, two)
        self.assertEqual(r['shared_nonzero_word3'], 1)
        self.assertEqual(r['identical_payload_when_word3_shared'], 0)
        self.assertEqual(r['same_reference_layout_when_word3_shared'], 1)

    def test_changed_named_target_but_same_payload(self):
        one = project_record(fixture())
        two = project_record(fixture())
        b = list(two['by_id'][0x11223344])
        b[3] = ((8, b'beta'),)
        two['by_id'][0x11223344] = tuple(b)
        r = compare(one, two)
        self.assertEqual(r['identical_payload_when_word3_shared'], 1)
        self.assertEqual(r['same_named_targets_when_word3_shared'], 0)

    def test_reference_target_offsets_independent_of_raw_payload(self):
        one = project_record(fixture())
        two = project_record(fixture())
        b = list(two['by_id'][0x11223344])
        b[4] = ((16, 1234),)
        two['by_id'][0x11223344] = tuple(b)
        r = compare(one, two)
        self.assertEqual(r['identical_payload_when_word3_shared'], 1)
        self.assertEqual(r['same_structured_target_offsets_when_word3_shared'], 0)

    def test_no_identifier_or_original_name_in_json_aggregates(self):
        one = project_record(fixture())
        encoded = json.dumps(compare(one, one))
        self.assertNotIn('alpha', encoded)
        self.assertNotIn('11223344', encoded)


if __name__ == '__main__':
    unittest.main()
