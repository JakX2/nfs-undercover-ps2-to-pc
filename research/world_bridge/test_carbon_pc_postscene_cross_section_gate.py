"""Synthetic-only cross-section tests; never use retail asset payloads."""
import json
import struct
import unittest
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from carbon_pc_postscene_dependency_probe import parse_pc_postscene
from carbon_pc_postscene_cross_section_gate import (
    _validate_record, independent_section_specificity, inspect_private_sources,
)


def chunk(tag, payload):
    return struct.pack('<II', tag, len(payload)) + payload


def make_record(hashes=(), scene=(), solid=(), groups=1, values=None,
                header_unknown=123, offset=2048, length=4096):
    if values is None:
        values = [{} for _ in range(groups)]
    header = struct.pack('<6I', 0x11111111, 0x11111111, groups,
                         groups, header_unknown, groups)
    out = bytearray(bytes(8) + chunk(0x37220,header))
    for i in range(groups):
        data = bytearray(120)
        pre = bytearray(12 if i == 0 else 8)
        end = bytearray(8)
        for (kind, idx), value in values[i].items():
            dst = {'data':data,'pre':pre,'end':end}[kind]
            struct.pack_into('<I', dst, 4*idx, value)
        out += chunk(0x37260,pre) + chunk(0x37250,data) + chunk(0x37270,end)
    parsed = parse_pc_postscene(bytes(out))
    return parsed, frozenset(scene or hashes), frozenset(solid or hashes), frozenset(), offset, length


def slot(report, kind='data', word=0):
    return next(x for x in report['field_slot_statistics']
                if x['record']==kind and x['word_index']==word)


class NegativeControlTests(unittest.TestCase):
    def test_two_independent_sections_support_a_local_only_slot(self):
        r1 = make_record(hashes={0xAAAA0201}, groups=6,
                         values=[{('data',0):0xAAAA0201}] + [{}]*5)
        r2 = make_record(hashes={0xBBBB0202},
                         values=[{('data',0):0xBBBB0202}])
        result = independent_section_specificity([r1,r2])
        row=slot(result)
        self.assertEqual(row['independent_source_sections_with_local_only_match'],2)
        self.assertEqual(row['local_only_occurrences'],2)
        self.assertTrue(row['passes_cross_section_followup_filter'])
        self.assertEqual(len(result['slots_passing_followup_filter']),1)

    def test_six_groups_in_only_one_section_not_independent(self):
        r=make_record(hashes={50}, groups=6,values=[{('data',0):50}]*6)
        row=slot(independent_section_specificity([r]))
        self.assertEqual(row['local_only_occurrences'],6)
        self.assertEqual(row['independent_source_sections_with_local_only_match'],1)
        self.assertFalse(row['passes_cross_section_followup_filter'])

    def test_foreign_only_control_blocks_followup(self):
        a=make_record(hashes={101}, values=[{('data',1):202}])
        b=make_record(hashes={202}, values=[{('data',1):101}])
        row=slot(independent_section_specificity([a,b]),word=1)
        self.assertEqual(row['foreign_only_occurrences'],2)
        self.assertEqual(row['local_only_occurrences'],0)
        self.assertFalse(row['passes_cross_section_followup_filter'])

    def test_shared_hash_cannot_disambiguate_its_section(self):
        a=make_record(hashes={101}, values=[{('data',1):101}])
        b=make_record(hashes={101}, values=[{('data',1):101}])
        report=independent_section_specificity([a,b])
        row=slot(report,word=1)
        self.assertEqual(row['ambiguous_shared_control_occurrences'],2)
        self.assertEqual(row['local_only_occurrences'],0)
        self.assertEqual(report['sections_with_any_shared_model_hash_in_other_section'],2)

    def test_only_one_section_local_and_other_zero_not_enough(self):
        a=make_record(hashes={101}, values=[{('data',1):101}])
        b=make_record(hashes={202})
        row=slot(independent_section_specificity([a,b]),word=1)
        self.assertEqual(row['independent_source_sections_with_local_only_match'],1)
        self.assertFalse(row['passes_cross_section_followup_filter'])

    def test_each_local_but_one_foreign_slot_not_pass(self):
        a=make_record(hashes={101}, groups=2,
                      values=[{('data',1):101},{('data',1):202}])
        b=make_record(hashes={202}, values=[{('data',1):202}])
        row=slot(independent_section_specificity([a,b]),word=1)
        self.assertEqual(row['local_only_occurrences'],2)
        self.assertEqual(row['foreign_only_occurrences'],1)
        self.assertFalse(row['passes_cross_section_followup_filter'])

    def test_scene_and_index_double_match_is_single_joint_bucket(self):
        a=make_record(scene={101},solid={101},values=[{('data',1):101}])
        b=make_record(scene={202},solid={202},values=[{('data',1):202}])
        report=independent_section_specificity([a,b]); row=slot(report,word=1)
        self.assertEqual(row['local_scene_and_solid_occurrences'],2)
        self.assertEqual(row['local_scene_only_occurrences'],0)
        self.assertEqual(row['local_solid_only_occurrences'],0)
        self.assertEqual(report['own_scene_and_solid_hash_set_overlap_counts'],[1,1])

    def test_scene_only_and_solid_only_distinguished(self):
        a=make_record(scene={101},solid={102},values=[{('data',1):101,('data',2):102}])
        b=make_record(scene={201},solid={202},values=[{('data',1):201,('data',2):202}])
        report=independent_section_specificity([a,b])
        self.assertEqual(slot(report,word=1)['local_scene_only_occurrences'],2)
        self.assertEqual(slot(report,word=2)['local_solid_only_occurrences'],2)

    def test_constant_sentinel_does_not_generate_false_hit(self):
        a=make_record(hashes={0x11111111},values=[{('data',1):0x11111111}])
        b=make_record(hashes={0xFFFFFFFF},values=[{('data',1):0xFFFFFFFF}])
        row=slot(independent_section_specificity([a,b]),word=1)
        self.assertEqual(row['sentinel_occurrences'],2)
        self.assertEqual(row['local_only_occurrences'],0)

    def test_zero_slot_never_claimed(self):
        row=slot(independent_section_specificity([make_record(hashes={0}),
                                                    make_record(hashes={0})]))
        self.assertEqual(row['zero_occurrences'],2)
        self.assertEqual(row['local_only_occurrences'],0)

    def test_first_group_extra_prelude_word_has_single_sample(self):
        a=make_record(hashes={101},groups=6,values=[{('pre',2):101}]+[{}]*5)
        b=make_record(hashes={202},values=[{('pre',2):202}])
        row=slot(independent_section_specificity([a,b]),kind='pre',word=2)
        self.assertEqual(row['local_only_occurrences'],2)
        self.assertEqual(row['zero_occurrences'],0)

    def test_opaque_source_values_excluded_from_json(self):
        a=make_record(hashes={0xDEADCAFE},values=[{('data',1):0xDEADCAFE}])
        report=independent_section_specificity([a])
        output=json.dumps(report)
        self.assertNotIn('DEADCAFE', output)
        self.assertNotIn(str(0xDEADCAFE), output)
        self.assertNotIn('2048', output)
        self.assertTrue(report['no_game_file_writes'])
        self.assertEqual(report['candidate_reference_semantics'],'UNVERIFIED')

    def test_no_values_in_empty_template(self):
        report=independent_section_specificity([make_record(),make_record()])
        self.assertEqual(report['slots_passing_followup_filter'],[])


class InputGateTests(unittest.TestCase):
    def test_no_sections(self):
        with self.assertRaisesRegex(ValueError,'1..100'):
            independent_section_specificity([])

    def test_over_100(self):
        with self.assertRaisesRegex(ValueError,'1..100'):
            independent_section_specificity([make_record()]*101)

    def test_bad_tuple(self):
        with self.assertRaisesRegex(ValueError,'tuple'):
            independent_section_specificity([tuple(range(4))])

    def test_bad_hash_type(self):
        a=list(make_record());a[1]=[123]
        with self.assertRaisesRegex(ValueError,'dimensions'):
            independent_section_specificity([tuple(a)])

    def test_out_of_range_hash(self):
        a=list(make_record());a[2]={2**40}
        with self.assertRaisesRegex(ValueError,'dimensions'):
            independent_section_specificity([tuple(a)])

    def test_invalid_length(self):
        a=list(make_record());a[5]=0
        with self.assertRaisesRegex(ValueError,'dimensions'):
            independent_section_specificity([tuple(a)])

    def test_bad_frame_word_count(self):
        a=list(make_record());a[0]=dict(a[0]);a[0]['header']=(1,)*6
        with self.assertRaisesRegex(ValueError,'header'):
            independent_section_specificity([tuple(a)])

    def test_bad_opaque_data_length(self):
        a=list(make_record());a[0]=dict(a[0]);groups=list(a[0]['groups']);groups[0]=dict(groups[0]);groups[0]['data']=bytes(119);a[0]['groups']=tuple(groups)
        with self.assertRaisesRegex(ValueError,'opaque'):
            independent_section_specificity([tuple(a)])

    def test_raw_file_does_not_exist(self):
        with self.assertRaises(ValueError):
            inspect_private_sources('/no/L5RB.BUN','/no/STREAML5RB.BUN')


class SyntheticPrivateFileTests(unittest.TestCase):
    def _fixture(self):
        from test_carbon_pc_postscene_dependency_probe import SyntheticEndToEndTests
        return SyntheticEndToEndTests().synthetic_helpers()

    def test_end_to_end_read_only_and_same_data_for_v1_v2(self):
        native, geometry, section = self._fixture()
        with TemporaryDirectory() as root:
            bun, stream = Path(root)/'L5RB.BUN', Path(root)/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128))
            stream.write_bytes(bytes(2048)+section)
            before=(bun.read_bytes(),stream.read_bytes())
            with patch.dict(sys.modules,{
                'carbon_pc_native_postscene_layout_gate':native,
                'geometry_hash_control':geometry,
            }):
                result = inspect_private_sources(bun,stream,(141,))
            self.assertEqual(before,(bun.read_bytes(),stream.read_bytes()))
            v1 = result['v1_field_correlations']
            v2 = result['v2_section_specificity']
            self.assertEqual(v1['inspected_native_sections'],1)
            self.assertEqual(v2['inspected_independent_sections'],1)
            self.assertEqual(slot(v2,word=0)['local_scene_only_occurrences'],1)
            self.assertEqual(slot(v2,word=1)['local_solid_only_occurrences'],1)
            self.assertEqual(v2['slots_passing_followup_filter'],[])
            self.assertFalse(result['runtime_tested'])

    def test_reject_duplicate_requested_ids_before_file_read(self):
        native, geometry, section = self._fixture()
        with TemporaryDirectory() as root:
            bun, stream = Path(root)/'L5RB.BUN',Path(root)/'STREAML5RB.BUN'
            bun.write_bytes(bytes(128))
            stream.write_bytes(bytes(2048)+section)
            with self.assertRaisesRegex(ValueError,'duplicate'):
                inspect_private_sources(bun,stream,(141,141))

    def test_reject_same_source_file_for_bun_and_stream(self):
        with TemporaryDirectory() as root:
            p=Path(root)/'archive.bin';p.write_bytes(bytes(128))
            with self.assertRaisesRegex(ValueError,'alias'):
                inspect_private_sources(p,p,(141,))

    def test_reject_symlink_source(self):
        with TemporaryDirectory() as root:
            real=Path(root)/'source';link=Path(root)/'alias'
            real.write_bytes(bytes(128));link.symlink_to(real)
            with self.assertRaisesRegex(ValueError,'regular'):
                inspect_private_sources(link,real,(141,))


if __name__ == '__main__':
    unittest.main()
