"""Synthetic only. No original game resources or game-file writes."""
import struct
import unittest
import tempfile
from pathlib import Path
from types import ModuleType
import sys
from unittest.mock import patch
from carbon_pc_postscene_dependency_probe import (
    HEAD, PRE, DATA, END, _frame, parse_pc_postscene,
    _word_samples, analyze_sections, inspect_original, _private_section_record)


def chunk(tag, payload):
    return struct.pack('<II', tag, len(payload)) + payload


def native_tail(groups=1, values=None, header_unknown=123):
    values = values or [{} for _ in range(groups)]
    head = struct.pack('<6I', 0x11111111, 0x11111111,
                       groups, groups, header_unknown, groups)
    tail = bytearray(bytes(8) + chunk(HEAD, head))
    for i in range(groups):
        pre = bytearray(12 if i == 0 else 8)
        data = bytearray(120)
        end = bytearray(8)
        for (kind, word), value in values[i].items():
            target = {'pre':pre, 'data':data, 'end':end}[kind]
            struct.pack_into('<I', target, 4*word, value)
        tail += chunk(PRE, pre) + chunk(DATA, data) + chunk(END, end)
    return bytes(tail)


def record(values=None, groups=1, scene_ids=frozenset(),
           solid_ids=frozenset(), anchors=frozenset(),
           disk_offset=2048, section_bytes=2048, header_unknown=123):
    parsed = parse_pc_postscene(native_tail(groups, values, header_unknown))
    return parsed, scene_ids, solid_ids, anchors, disk_offset, section_bytes


class ParserTests(unittest.TestCase):
    def test_known_one_group_204_bytes(self):
        raw = native_tail()
        self.assertEqual(len(raw), 204)
        obj = parse_pc_postscene(raw)
        self.assertEqual(len(obj['groups']), 1)
        self.assertEqual(len(obj['groups'][0]['pre']), 12)
        self.assertEqual(len(obj['groups'][0]['data']), 120)
        self.assertEqual(len(obj['groups'][0]['end']), 8)

    def test_known_six_groups_1004_bytes(self):
        raw = native_tail(6)
        self.assertEqual(len(raw), 1004)
        obj = parse_pc_postscene(raw)
        self.assertEqual([len(x['pre']) for x in obj['groups']], [12,8,8,8,8,8])

    def test_frame_cannot_truncate(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            _frame(b'\x00'*7, 0, HEAD, 24)

    def test_bad_prefix(self):
        with self.assertRaisesRegex(ValueError, 'prefix'):
            parse_pc_postscene(b'\x01'+native_tail()[1:])

    def test_bad_header_length(self):
        b = bytearray(native_tail())
        struct.pack_into('<I', b, 12, 23)
        with self.assertRaisesRegex(ValueError, 'tag or length'):
            parse_pc_postscene(bytes(b))

    def test_bad_header_repeated_count(self):
        b = bytearray(native_tail())
        struct.pack_into('<I', b, 8+8+3*4, 2)
        with self.assertRaisesRegex(ValueError, 'count'):
            parse_pc_postscene(bytes(b))

    def test_too_many_groups_rejected(self):
        b = bytearray(native_tail())
        struct.pack_into('<I', b, 8+8+2*4, 65)
        with self.assertRaisesRegex(ValueError, 'count'):
            parse_pc_postscene(bytes(b))

    def test_bad_data_id(self):
        b = bytearray(native_tail())
        b[60:64] = struct.pack('<I', 0xDEADBEEF)
        with self.assertRaisesRegex(ValueError, 'tag or length'):
            parse_pc_postscene(bytes(b))

    def test_bad_data_size(self):
        b = bytearray(native_tail())
        struct.pack_into('<I', b, 64, 124)
        with self.assertRaisesRegex(ValueError, 'tag or length'):
            parse_pc_postscene(bytes(b))

    def test_extra_trailing(self):
        with self.assertRaisesRegex(ValueError, 'trailing'):
            parse_pc_postscene(native_tail() + b'\x00'*4)

    def test_truncated_last_record(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            parse_pc_postscene(native_tail()[:-1])

    def test_reject_unsupported_type(self):
        with self.assertRaises(ValueError):
            parse_pc_postscene(bytearray(native_tail()))


class CorrelationTests(unittest.TestCase):
    def test_exact_hash_joins(self):
        samples = list(_word_samples(
            parse_pc_postscene(native_tail(values=[{('data',0):0x12345,
                                                     ('data',1):0x789AB}])),
            {0x12345}, {0x789AB}, set(), 2048, 512))
        self.assertTrue(any(
            key==('data',0) and flags['scene_hash'] for key,_,flags in samples))
        self.assertTrue(any(key==('data',1) and flags['indexed_solid_hash']
                            for key,_,flags in samples))

    def test_exact_relative_and_absolute_root_anchors(self):
        samples = list(_word_samples(
            parse_pc_postscene(native_tail(values=[{('data',0):256,
                                                     ('data',1):2048+512}])),
            set(),set(),{256,512},2048,1024))
        flags = {key: f for key,_,f in samples}
        self.assertTrue(flags[('data',0)]['exact_relative_anchor'])
        self.assertTrue(flags[('data',1)]['exact_absolute_anchor'])

    def test_zero_never_matches_even_with_zero_source(self):
        obj = record(scene_ids={0}, solid_ids={0}, anchors={0}, disk_offset=0)
        results = list(_word_samples(*obj))
        self.assertTrue(all(f['zero'] for _,_,f in results))
        self.assertFalse(any(f['scene_hash'] or f['indexed_solid_hash']
                             or f['exact_relative_anchor'] or f['exact_absolute_anchor']
                             for _,_,f in results))

    def test_sentinels_excluded_from_correlation(self):
        rec = record(values=[{('data',0):0xFFFFFFFF, ('data',1):0x11111111}],
                     scene_ids={0xFFFFFFFF,0x11111111},
                     solid_ids={0xFFFFFFFF,0x11111111})
        a = {(k):flags for k,_,flags in _word_samples(*rec)}
        self.assertFalse(a[('data',0)]['scene_hash'])
        self.assertFalse(a[('data',1)]['indexed_solid_hash'])

    def test_aligned_ranges_are_candidates_not_pointer_claims(self):
        rec = record(values=[{('data',0):128, ('data',1):2048+128}],
                     section_bytes=512, disk_offset=2048)
        result = analyze_sections([rec])
        slot = [r for r in result['field_slot_statistics']
                if r['record']=='data' and r['word_index']==0][0]
        self.assertEqual(slot['aligned_in_section_range_candidates'],1)
        self.assertEqual(result['pointers_and_relocation'],'UNVERIFIED')

    def test_field_counts_with_distinct_values(self):
        rec = record(values=[{('data',0):14}, {('data',0):22}], groups=2)
        output = analyze_sections([rec])
        slot = next(r for r in output['field_slot_statistics']
                    if (r['record'],r['word_index'])==('data',0))
        self.assertEqual((slot['sample_count'],slot['distinct_nonzero_values']),(2,2))

    def test_duplicate_payload_occurrence(self):
        output = analyze_sections([record(groups=2),record(groups=1)])
        self.assertEqual(output['duplicate_120_byte_payload_occurrences'],2)
        self.assertEqual(output['inspected_native_groups'],3)

    def test_unknown_header_word_has_no_interpreted_value(self):
        output = analyze_sections([record(header_unknown=123),record(header_unknown=456)])
        self.assertEqual(output['distinct_unknown_header_word4_values'],2)
        self.assertNotIn('123',str(output))
        self.assertNotIn('456',str(output))

    def test_reject_empty_input(self):
        with self.assertRaisesRegex(ValueError,'between 1 and 100'):
            analyze_sections([])

    def test_reject_over_100(self):
        with self.assertRaisesRegex(ValueError,'between 1 and 100'):
            analyze_sections([record()]*101)

    def test_reject_invalid_disk_section_range(self):
        with self.assertRaisesRegex(ValueError,'range'):
            list(_word_samples(parse_pc_postscene(native_tail()),set(),set(),set(),-1,2048))

    def test_invalid_filename_fails_closed(self):
        with self.assertRaises(ValueError):
            inspect_original('/nonexistent/L5RB.BUN','/nonexistent/STREAML5RB.BUN')

    def test_no_source_values_in_aggregate_json(self):
        obj = analyze_sections([record(values=[{('data',0):0xABCD1234}],
                                       scene_ids={0xABCD1234})])
        data = str(obj)
        self.assertNotIn('ABCD1234',data)
        self.assertNotIn(str(0xABCD1234),data)
        self.assertTrue(obj['no_game_file_writes'])


class SyntheticEndToEndTests(unittest.TestCase):
    def synthetic_helpers(self, scene_hash=0xAABBCCDD, platform=0x00134900):
        # Minimal synthetic namespace mirrors the existing modules' contracts.
        native = ModuleType('carbon_pc_native_postscene_layout_gate')
        geometry = ModuleType('geometry_hash_control')
        records = bytearray(72)
        struct.pack_into('<II', records, 0x18, scene_hash, scene_hash)
        scene = chunk(0x80034100, chunk(0x34102, bytes(records)))
        tail = native_tail(values=[{('data',0):scene_hash,('data',1):0x12345678}])
        section = bytes(32) + scene + tail
        def children(blob, start, end):
            at = start
            while at < end:
                tag, count = struct.unpack_from('<II', blob, at)
                yield tag, at+8, at+8+count
                at += 8+count
            if at != end: raise ValueError('bad child')
        def scan(_blob, geom_count):
            if geom_count != 1: raise ValueError('bad geometry count')
            return {'texture_root_bytes':16, 'geometry_root_bytes':(16,),
                    'interroot_zero_chunk_bytes':0, 'scene':scene,
                    'scene_end':32+len(scene), 'postscene':tail}
        native._children = children
        native._scan_roots = scan
        native.profile_carbon_section = lambda _blob: {'section_bytes':len(_blob)}
        native.stream_rows = lambda _bun, _stream_size: {141:(2048,len(section))}
        geometry.parse_geometry_root = lambda _blob: {
            'platform':platform, 'hashes':frozenset((0x12345678,))}
        return native, geometry, section

    def test_one_section_read_only_with_fake_dependencies(self):
        native, geometry, section = self.synthetic_helpers()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            bun = p/'L5RB.BUN'; stream = p/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128))
            stream.write_bytes(bytes(2048) + section)
            baseline = [x.read_bytes() for x in (bun,stream)]
            with patch.dict(sys.modules, {
                'carbon_pc_native_postscene_layout_gate':native,
                'geometry_hash_control':geometry}):
                report = inspect_original(bun,stream,section_ids=(141,))
            self.assertEqual([x.read_bytes() for x in (bun,stream)], baseline)
            self.assertEqual(report['inspected_native_groups'],1)
            slot0 = next(row for row in report['field_slot_statistics']
                         if row['record']=='data' and row['word_index']==0)
            slot1 = next(row for row in report['field_slot_statistics']
                         if row['record']=='data' and row['word_index']==1)
            self.assertEqual(slot0['matching_scene_model_hashes'],1)
            self.assertEqual(slot1['matching_geometry_index_hashes'],1)

    def test_native_pc_platform_required(self):
        native, geometry, section = self.synthetic_helpers(platform=0x00134A00)
        with patch.dict(sys.modules, {
            'carbon_pc_native_postscene_layout_gate':native,
            'geometry_hash_control':geometry}):
            with self.assertRaisesRegex(ValueError,'not Carbon PC'):
                _private_section_record(section,2048)

    def test_reject_unlisted_section_in_private_stream(self):
        native, geometry, section = self.synthetic_helpers()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            bun = p/'L5RB.BUN'; stream = p/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128)); stream.write_bytes(bytes(2048)+section)
            with patch.dict(sys.modules, {
                'carbon_pc_native_postscene_layout_gate':native,
                'geometry_hash_control':geometry}):
                with self.assertRaisesRegex(ValueError,'missing'):
                    inspect_original(bun,stream,(999,))

    def test_reject_duplicate_requested_sections(self):
        native, geometry, section = self.synthetic_helpers()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            bun = p/'L5RB.BUN'; stream = p/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128)); stream.write_bytes(bytes(2048)+section)
            with patch.dict(sys.modules, {
                'carbon_pc_native_postscene_layout_gate':native,
                'geometry_hash_control':geometry}):
                with self.assertRaisesRegex(ValueError,'duplicate'):
                    inspect_original(bun,stream,(141,141))


if __name__ == '__main__':
    unittest.main()
