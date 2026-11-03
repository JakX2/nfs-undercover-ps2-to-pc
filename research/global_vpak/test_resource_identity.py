"""Pure synthetic tests of NpeD identity parsing and matching."""
import struct
import unittest

from resource_identity import parse_resource_key, compare_resources, index_resources


def npe(base='gpcore', h1=111, h2=222):
    a = (base + '.vlt').encode('ascii') + b'\0'
    b = (base + '.bin').encode('ascii') + b'\0'
    assert len(a) == len(b)
    data = b'NpeD' + struct.pack('<6I', 0, 2, h1, h2, 0, len(a)) + a + b
    data += b'\0' * (-len(data) % 16)
    return data[:4] + struct.pack('<I', len(data)) + data[8:]


def record(chunk):
    return {'chunks': {'NpeD': chunk, 'NpxE': b'\0' * 48}}


class ResourceIdentityTests(unittest.TestCase):
    def test_parse_valid(self):
        self.assertEqual(parse_resource_key(npe()), {'base': 'gpcore', 'hash_pair': (111, 222)})

    def test_reject_mismatched_resource_pair(self):
        b = bytearray(npe())
        ix = b.index(b'.bin\0')
        b[ix - 1] ^= 1
        with self.assertRaisesRegex(ValueError, 'Mismatched'):
            parse_resource_key(bytes(b))

    def test_reject_invalid_header(self):
        b = bytearray(npe())
        struct.pack_into('<I', b, 8, 3)
        with self.assertRaisesRegex(ValueError, 'header'):
            parse_resource_key(bytes(b))

    def test_reject_name_length(self):
        b = bytearray(npe())
        struct.pack_into('<I', b, 24, 0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError, 'filename size'):
            parse_resource_key(bytes(b))

    def test_reject_nonzero_padding(self):
        b = bytearray(npe())
        b[-1] = 1
        with self.assertRaisesRegex(ValueError, 'padding'):
            parse_resource_key(bytes(b))

    def test_reject_embedded_null(self):
        b = bytearray(npe('race_bin_quickrace'))
        b[30] = 0
        with self.assertRaises(ValueError):
            parse_resource_key(bytes(b))

    def test_reject_duplicate_keys(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            index_resources([record(npe()), record(npe())])

    def test_cross_index_match_and_hash_mismatch(self):
        a = index_resources([record(npe('alpha')), record(npe('gpcore'))])
        b = index_resources([record(npe('gpcore', 111, 333)), record(npe('beta'))])
        c = compare_resources(a, b)
        self.assertEqual((c['shared_resource_pairs'], c['same_index_pairs'], c['matching_hash_pairs']), (1, 0, 0))
        self.assertEqual(c['shared'][0]['name'], 'gpcore')


if __name__ == '__main__':
    unittest.main()
