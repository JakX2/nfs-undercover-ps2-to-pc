"""Synthetic-only regressions for cross-platform VPAK field normalization."""
import struct
import unittest

from wii_gameplay_bridge import parse_gameplay, compare_records, TAGS


def make_vpak(wii=False, marker=0x1234):
    fmt = '>' if wii else '<'
    pool = b'alpha\0\0\0'
    assert len(pool) == 8
    text = (b'StrE' if wii else b'ErtS') + struct.pack(fmt + 'I', 16) + pool
    aux = bytearray()
    for tag in TAGS:
        if tag == 'NpeD':
            body = struct.pack(fmt + '5I', 2, 17, 19, 0, 6) + b'r.vlt\0r.bin\0'
        elif tag == 'NpxE':
            body = struct.pack(fmt + '2I', 1, 0) + struct.pack(fmt + '4I', 0x8e112eb7, 16, 120, marker)
        elif tag == 'NrtP':
            rows = [(0, 0x10002, 0), (20, 0x10003, 8), (0, 2, 0), (108, 0x10003, 8), (0, 0, 0)]
            if wii:
                rows = [(a, ((b & 0xffff) << 16) | (b >> 16), c) for a, b, c in rows]
            body = b''.join(struct.pack(fmt + '3I', *r) for r in rows)
        else:
            body = b'\0' * 8
        payload = tag.encode('ascii')[::-1] if wii else tag.encode('ascii')
        n = (8 + len(body) + 15) // 16 * 16
        aux += payload + struct.pack(fmt + 'I', n) + body + b'\0' * (n - 8 - len(body))
    index_end = 36
    index = struct.pack('<5I', 0, len(text), len(aux), index_end, index_end + len(text))
    return b'VPAK' + struct.pack('<3I', 1, index_end, 0) + index + text + aux


class WiiGameplayBridgeTests(unittest.TestCase):
    def test_normalize_wii_ps2(self):
        a, b = parse_gameplay(make_vpak(True), True), parse_gameplay(make_vpak(), False)
        result = compare_records(a, b)
        for key in ('index_matching_records', 'pool_matching_records', 'name_tail_matching_records',
                    'exports_matching_records', 'references_matching_records'):
            self.assertEqual(result[key], 1, key)
        self.assertEqual(result['shared_export_entries_numerically_equal'], 1)

    def test_one_export_record(self):
        self.assertEqual(len(parse_gameplay(make_vpak(True), True)[0]['exports']), 1)

    def test_mismatched_marker_is_detected(self):
        a, b = parse_gameplay(make_vpak(True, marker=44), True), parse_gameplay(make_vpak(marker=45))
        self.assertEqual(compare_records(a, b)['exports_matching_records'], 0)

    def test_reject_wrong_endianness(self):
        with self.assertRaises(ValueError):
            parse_gameplay(make_vpak(True), False)

    def test_reject_no_vpak(self):
        with self.assertRaisesRegex(ValueError, 'VPAK header'):
            parse_gameplay(b'????' + make_vpak()[4:])

    def test_reject_bad_index_count(self):
        data = bytearray(make_vpak())
        struct.pack_into('<I', data, 4, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'VPAK index'):
            parse_gameplay(bytes(data))

    def test_reject_bad_erts_tag(self):
        data = bytearray(make_vpak())
        data[36:40] = b'WRNG'
        with self.assertRaisesRegex(ValueError, 'string header'):
            parse_gameplay(bytes(data))

    def test_reject_bad_aux_tag(self):
        data = bytearray(make_vpak(True))
        data[52:56] = b'WRNG'
        with self.assertRaisesRegex(ValueError, 'sreV chunk'):
            parse_gameplay(bytes(data), True)

    def test_reject_bad_export_count(self):
        data = bytearray(make_vpak())
        pos = data.find(b'NpxE')
        struct.pack_into('<I', data, pos + 8, 999)
        with self.assertRaisesRegex(ValueError, 'NpxE entry count'):
            parse_gameplay(bytes(data))

    def test_reject_unknown_nrtp_marker(self):
        data = bytearray(make_vpak())
        pos = data.find(b'NrtP')
        struct.pack_into('<I', data, pos + 8 + 4, 0xdeadbeef)
        with self.assertRaisesRegex(ValueError, 'Unknown NrtP marker'):
            parse_gameplay(bytes(data))

    def test_reject_nonzero_terminator_padding(self):
        data = bytearray(make_vpak(True))
        pos = data.find(b'PtrN')
        data[pos + 8 + 5 * 12] = 1
        with self.assertRaisesRegex(ValueError, 'Nonzero NrtP padding'):
            parse_gameplay(bytes(data), True)

    def test_record_total_mismatch(self):
        a = parse_gameplay(make_vpak(True), True)
        self.assertEqual(compare_records(a, [])['compared_records'], 0)


if __name__ == '__main__':
    unittest.main()
