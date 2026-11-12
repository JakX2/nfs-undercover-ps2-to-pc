"""Synthetic-only V3 controls. No game file bytes or proprietary fixtures."""
import json
import struct
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from test_carbon_pc_postscene_cross_section_gate import make_record
from carbon_pc_postscene_lane_controls import (
    _check_independence, _classify, _lane_words, audit_byte_lanes,
    strict_slot_screen, inspect_private_sources,
)


def rec(i, keys=(), values=None, groups=1):
    return make_record(hashes=set(keys), values=values, groups=groups,
                       offset=2048 + 8192*i, length=4096)


def lane_row(report, kind='data', endian='little', lane=0):
    return next(r for r in report['field_byte_lane_statistics']
                if (r['record'], r['byte_order'], r['byte_lane']) ==
                (kind, endian, lane))


def strict_row(report, kind='data', slot=0):
    return next(r for r in report['field_slot_statistics']
                if (r['record'], r['word_index']) == (kind, slot))


class ClassificationTests(unittest.TestCase):
    def test_zero_never_hash(self):
        self.assertEqual(_classify(0,{0},set()),'zero')

    def test_magic_ones_never_hash(self):
        self.assertEqual(_classify(0x11111111,{0x11111111},set()),'sentinel')

    def test_all_ones_never_hash(self):
        self.assertEqual(_classify(0xffffffff,{0xffffffff},set()),'sentinel')

    def test_exclusive_local(self):
        self.assertEqual(_classify(32,{32},{21}),'local_only')

    def test_exclusive_foreign(self):
        self.assertEqual(_classify(21,{32},{21}),'foreign_only')

    def test_shared(self):
        self.assertEqual(_classify(32,{32},{32}),'shared')

    def test_unmatched(self):
        self.assertEqual(_classify(44,{32},{21}),'unmatched')


class LaneDecodeTests(unittest.TestCase):
    def test_exact_little_endian(self):
        buf=struct.pack('<II',0xA1B2C3D4,0x11223344)
        self.assertEqual(list(_lane_words(buf,'little',0)),[0xA1B2C3D4,0x11223344])

    def test_big_endian_changes_value(self):
        buf=struct.pack('<I',0xA1B2C3D4)
        self.assertEqual(list(_lane_words(buf,'big',0)),[0xD4C3B2A1])

    def test_shifted_lanes_are_not_same_data(self):
        buf=struct.pack('<II',0xA1B2C3D4,0x11223344)
        self.assertEqual(len(list(_lane_words(buf,'little',0))),2)
        self.assertEqual(len(list(_lane_words(buf,'little',1))),1)
        self.assertNotEqual(list(_lane_words(buf,'little',1)),
                            list(_lane_words(buf,'little',0)))

    def test_under_four_byte_payload_yields_none(self):
        self.assertEqual(list(_lane_words(b'abc','little',0)),[])


class ByteLaneAuditTests(unittest.TestCase):
    def test_only_aligned_little_endian_gets_local_hit(self):
        a=rec(0,{0xA1B2C3D4},[{('data',0):0xA1B2C3D4}])
        b=rec(1,{0xABCD1234},[{('data',0):0xABCD1234}])
        r=audit_byte_lanes([a,b])
        self.assertEqual(lane_row(r)['local_only_hash_matches'],2)
        for endian, shift in (('big',0),('little',1),('little',2),('little',3)):
            self.assertEqual(lane_row(r,endian=endian,lane=shift)['local_only_hash_matches'],0)

    def test_one_foreign_hit_is_not_local(self):
        a=rec(0,{0xA1B2C3D4},[{('data',1):0xABCD1234}])
        b=rec(1,{0xABCD1234},[{}])
        r=audit_byte_lanes([a,b])
        self.assertEqual(lane_row(r)['foreign_only_hash_matches'],1)

    def test_shared_hash_is_ambiguous(self):
        a=rec(0,{0xABCD1234},[{('data',1):0xABCD1234}])
        b=rec(1,{0xABCD1234},[{('data',1):0xABCD1234}])
        self.assertEqual(lane_row(audit_byte_lanes([a,b]))['shared_hash_matches'],2)

    def test_sentinels_never_count_as_matches(self):
        a=rec(0,{0x11111111,0xffffffff},[{('data',1):0x11111111}])
        r=audit_byte_lanes([a])
        self.assertEqual(lane_row(r)['sentinel_words'],1)
        self.assertEqual(lane_row(r)['local_only_hash_matches'],0)

    def test_independent_section_support_not_group_occurrences(self):
        a=rec(0,{0xABCD1234},[{('data',1):0xABCD1234}]*6,groups=6)
        b=rec(1,{0xBCDE2345},[{}])
        row=lane_row(audit_byte_lanes([a,b]))
        self.assertEqual(row['local_only_hash_matches'],6)
        self.assertEqual(row['sections_with_local_only_hash_match'],1)

    def test_all_five_lanes_each_kind(self):
        result=audit_byte_lanes([rec(0)])
        self.assertEqual(len(result['field_byte_lane_statistics']),15)
        self.assertEqual(sum(x['is_predeclared_negative_control']
                             for x in result['field_byte_lane_statistics']),12)

    def test_data_payload_lanes_have_30_and_29_words(self):
        r=audit_byte_lanes([rec(0)])
        self.assertEqual(lane_row(r)['tested_words'],30)
        self.assertEqual(lane_row(r,endian='little',lane=3)['tested_words'],29)

    def test_extra_first_prelude_word_not_silently_dropped(self):
        a=rec(0,{0xA1B2C3D4},[{('pre',2):0xA1B2C3D4},{}],groups=2)
        self.assertEqual(lane_row(audit_byte_lanes([a]),kind='pre')['tested_words'],5)

    def test_no_private_hashes_or_offsets_in_report(self):
        r=audit_byte_lanes([rec(0,{0xDEADCAFE},[{('data',4):0xDEADCAFE}])])
        report=json.dumps(r)
        self.assertNotIn('DEADCAFE',report)
        self.assertNotIn(str(0xDEADCAFE),report)
        self.assertNotIn('2048',report)
        self.assertTrue(r['no_game_file_writes'])
        self.assertFalse(r['game_runtime_tested'])


class StrictScreenTests(unittest.TestCase):
    def test_three_clean_independent_sections_pass(self):
        records=[rec(i,{0xA1B2C3D4+i},[{('data',2):0xA1B2C3D4+i}])
                 for i in range(3)]
        r=strict_slot_screen(records)
        self.assertTrue(strict_row(r,slot=2)['passes_strict_three_section_screen'])
        self.assertEqual(r['strict_screen_candidates'],[{'record':'data','word_index':2}])

    def test_two_sections_no_overclaim(self):
        r=strict_slot_screen([rec(i,{900+i},[{('data',2):900+i}])
                              for i in range(2)])
        self.assertTrue(r['insufficient_independent_sections_for_pass'])
        self.assertFalse(strict_row(r,slot=2)['passes_strict_three_section_screen'])

    def test_single_section_multiple_groups_not_independent(self):
        r=strict_slot_screen([rec(0,{99},[{('data',2):99}]*6,groups=6)])
        self.assertEqual(strict_row(r,slot=2)['independent_sections_with_local_only_match'],1)
        self.assertEqual(r['strict_screen_candidates'],[])

    def test_two_local_hits_plus_unmatched_blocks_pass(self):
        records=[rec(i,{201+i},[{('data',2):201+i if i<2 else 8080}])
                 for i in range(3)]
        r=strict_slot_screen(records)
        row=strict_row(r,slot=2)
        self.assertEqual((row['local_only_hits'],row['informative_words']),(2,3))
        self.assertFalse(row['passes_strict_three_section_screen'])

    def test_one_foreign_in_extra_group_blocks_pass(self):
        records=[rec(0,{101},[{('data',1):101},{('data',1):202}],groups=2),
                 rec(1,{202},[{('data',1):202}]),
                 rec(2,{303},[{('data',1):303}])]
        self.assertFalse(strict_row(strict_slot_screen(records),slot=1)
                         ['passes_strict_three_section_screen'])

    def test_shared_model_hash_blocks_pass(self):
        records=[rec(i,{101},[{('data',2):101}]) for i in range(3)]
        self.assertFalse(strict_row(strict_slot_screen(records),slot=2)
                         ['passes_strict_three_section_screen'])

    def test_zero_and_sentinal_excluded_from_denominator(self):
        records=[rec(0,{101},[{('data',2):101},{}],groups=2),
                 rec(1,{102},[{('data',2):102}]),
                 rec(2,{103},[{('data',2):103}])]
        r=strict_slot_screen(records)
        self.assertEqual(strict_row(r,slot=2)['informative_words'],3)
        self.assertTrue(strict_row(r,slot=2)['passes_strict_three_section_screen'])

    def test_no_nonzero_does_not_pass(self):
        r=strict_slot_screen([rec(i) for i in range(3)])
        self.assertFalse(strict_row(r)['all_informative_words_local_only'])
        self.assertEqual(r['strict_screen_candidates'],[])

    def test_fewer_than_three_local_support_sections_fails(self):
        records=[rec(0,{101},[{('data',1):101}]),
                 rec(1,{102},[{('data',1):102}]),rec(2,{103})]
        self.assertFalse(strict_row(strict_slot_screen(records),slot=1)
                         ['passes_strict_three_section_screen'])

    def test_three_sections_four_matching_occurrences_pass(self):
        records=[rec(0,{101},[{('data',1):101},{('data',1):101}],groups=2),
                 rec(1,{102},[{('data',1):102}]),
                 rec(2,{103},[{('data',1):103}])]
        r=strict_slot_screen(records)
        self.assertEqual(strict_row(r,slot=1)['local_only_hits'],4)
        self.assertTrue(strict_row(r,slot=1)['passes_strict_three_section_screen'])


class AuditIndependenceTests(unittest.TestCase):
    def test_duplicate_ranges_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlap'):
            _check_independence([rec(0),rec(0)])

    def test_overlapping_distinct_starts_rejected(self):
        a=rec(0); b=list(rec(1)); b[4]=4096
        with self.assertRaisesRegex(ValueError,'overlap'):
            audit_byte_lanes([a,tuple(b)])

    def test_unaligned_section_rejected(self):
        a=list(rec(0)); a[4]=2049
        with self.assertRaisesRegex(ValueError,'aligned'):
            audit_byte_lanes([tuple(a)])

    def test_outside_32bit_stream_rejected(self):
        a=list(rec(0)); a[4]=0xfffff800
        with self.assertRaisesRegex(ValueError,'32-bit'):
            strict_slot_screen([tuple(a)])

    def test_no_records_rejected(self):
        with self.assertRaisesRegex(ValueError,'1..100'):
            audit_byte_lanes([])

    def test_over_100_rejected(self):
        with self.assertRaisesRegex(ValueError,'1..100'):
            strict_slot_screen([rec(i) for i in range(101)])

    def test_malformed_header_rejected(self):
        a=list(rec(0)); a[0]=dict(a[0]); a[0]['header']=(0,)*6
        with self.assertRaisesRegex(ValueError,'header'):
            audit_byte_lanes([tuple(a)])

    def test_malformed_payload_rejected(self):
        a=list(rec(0)); a[0]=dict(a[0]);g=list(a[0]['groups']);g[0]=dict(g[0]);g[0]['data']=b'\x00'*119;a[0]['groups']=tuple(g)
        with self.assertRaisesRegex(ValueError,'opaque'):
            audit_byte_lanes([tuple(a)])

    def test_reject_file_missing(self):
        with self.assertRaisesRegex(ValueError,'regular'):
            inspect_private_sources('/missing/L5RB.BUN','/missing/STREAML5RB.BUN')

    def test_reject_duplicate_section_args(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            inspect_private_sources('/missing/L5RB.BUN','/missing/STREAML5RB.BUN',(141,141))


class EndToEndPrivateFixtureTests(unittest.TestCase):
    def _fixture(self):
        from test_carbon_pc_postscene_dependency_probe import SyntheticEndToEndTests
        return SyntheticEndToEndTests().synthetic_helpers()

    def test_synthetic_read_without_modification(self):
        native, geometry, section = self._fixture()
        with TemporaryDirectory() as d:
            bun, stream = Path(d)/'L5RB.BUN',Path(d)/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128)); stream.write_bytes(bytes(2048)+section)
            before=(bun.read_bytes(),stream.read_bytes())
            with patch.dict(sys.modules,{
                'carbon_pc_native_postscene_layout_gate':native,
                'geometry_hash_control':geometry,
            }):
                report=inspect_private_sources(bun,stream,(141,))
            self.assertEqual(before,(bun.read_bytes(),stream.read_bytes()))
            self.assertEqual(report['v3_lane_controls']['independent_nonoverlapping_sections'],1)
            self.assertTrue(report['v3_strict_screen']['insufficient_independent_sections_for_pass'])
            self.assertEqual(report['original_files_written'],False)
            self.assertEqual(report['runtime_claim'],'NONE')

    def test_source_alias_is_rejected(self):
        with TemporaryDirectory() as d:
            x=Path(d)/'same'; x.write_bytes(b'abc')
            with self.assertRaisesRegex(ValueError,'alias'):
                inspect_private_sources(x,x,(141,))

    def test_symlink_is_rejected(self):
        with TemporaryDirectory() as d:
            x=Path(d)/'real'; y=Path(d)/'sym'; x.write_bytes(b'abc'); y.symlink_to(x)
            with self.assertRaisesRegex(ValueError,'regular'):
                inspect_private_sources(y,x,(141,))


if __name__ == '__main__':
    unittest.main()
