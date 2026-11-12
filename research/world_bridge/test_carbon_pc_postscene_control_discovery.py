"""V4 synthetic-only blind-scan tests. Never read, modify or include game assets."""
import json
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_carbon_pc_postscene_cross_section_gate import make_record
import carbon_pc_postscene_control_discovery as gate


def fake_fixture(ids=(141, 142, 143), non_pc=(), malformed=(), duplicates=(),
                 empty=(), hashes=None, bad_baseline=False):
    """Create a fake indexed stream, not a proprietary Carbon resource."""
    assert ids
    b = bytearray(128)
    offsets = {}
    payloads = {}
    for pos, sec in enumerate(ids):
        offset = 2048 * (pos + 1)
        payload = (struct.pack('<I', 0x11112222 if sec in non_pc else gate.PC_TEXTURE_TAG)
                   + struct.pack('<I', sec & 0xffffffff) + bytes(56))
        offsets[sec] = (offset, 0 if sec in empty else len(payload))
        payloads[sec] = payload
        if len(b) < offset: b.extend(bytes(offset-len(b)))
        b.extend(payload)
    tmp = TemporaryDirectory()
    p = Path(tmp.name)
    bun = p/'L5RB.BUN'; stream = p/'STREAML5RB.BUN'
    bun.write_bytes(b'INDEX-STUB'); stream.write_bytes(b)

    def source_record(section, offset):
        sid = struct.unpack_from('<I', section, 4)[0]
        if sid in malformed or (bad_baseline and sid == 141):
            raise ValueError('Synthetic malformed resource envelope')
        if sid == 999:
            raise RuntimeError('Unexpected parser bug')
        match = (hashes or {}).get(sid, 0xA0010000+sid)
        values = [{('data', 2): match}]
        record = make_record(hashes={match}, values=values,
                             offset=offset, length=len(section),
                             header_unknown=444)
        if sid in duplicates:
            record = make_record(hashes={match}, values=[{('data',2):0}],
                                 offset=offset, length=len(section),
                                 header_unknown=444)
        return record
    return tmp, bun, stream, offsets, source_record


def execute(ids=(141,142,143), **kwargs):
    tmp, bun, stream, table, fake_parser = fake_fixture(ids=ids, **kwargs)
    try:
        before = (bun.read_bytes(),stream.read_bytes())
        with patch.dict(sys.modules, {'carbon_pc_native_postscene_layout_gate':
                                      SimpleNamespace(stream_rows=lambda data, size: table)}), \
             patch.object(gate,'_private_section_record', side_effect=fake_parser):
            report = gate.inspect_originals(bun,stream)
        assert before == (bun.read_bytes(),stream.read_bytes())
        return report
    finally:
        tmp.cleanup()


class EndToEndDiscoveryTests(unittest.TestCase):
    def test_automatically_finds_third_valid_control(self):
        r = execute()
        self.assertEqual(r['strictly_authenticated_section_ids'],[141,142,143])
        self.assertEqual(r['independent_distinct_suffix_section_ids'],[141,142,143])
        self.assertEqual(r['independent_three_section_gate'],'EVALUABLE')
        self.assertEqual(r['first_additional_control_beyond_baselines'],143)
        self.assertEqual(r['v3_strict_screen']['strict_screen_candidates'],
                         [{'record':'data','word_index':2}])
        self.assertFalse(r['game_file_write_performed'])
        self.assertFalse(r['retail_game_execution_tested'])

    def test_two_controls_insufficient(self):
        r = execute(ids=(141,142))
        self.assertEqual(r['independent_three_section_gate'],'INSUFFICIENT_CONTROLS')
        self.assertIsNone(r['first_additional_control_beyond_baselines'])
        self.assertTrue(r['v3_strict_screen']['insufficient_independent_sections_for_pass'])

    def test_ignores_non_pc_texture_root_prefix(self):
        r=execute(ids=(141,142,143,144),non_pc=(143,))
        self.assertEqual(r['indexed_row_census']['outside_texture_root_prefix'],1)
        self.assertEqual(r['first_additional_control_beyond_baselines'],144)

    def test_invalid_full_structure_is_rejected_not_counted(self):
        r=execute(ids=(141,142,143,144),malformed=(143,))
        self.assertEqual(r['indexed_row_census']['unsupported_by_current_strict_profile'],1)
        self.assertEqual(r['first_additional_control_beyond_baselines'],144)

    def test_fails_closed_when_baseline_has_invalid_full_structure(self):
        with self.assertRaisesRegex(ValueError,'baseline failed'):
            execute(ids=(141,142,143), malformed=(141,))

    def test_fails_closed_when_baseline_missing_from_index(self):
        with self.assertRaisesRegex(ValueError,'missing from source index'):
            execute(ids=(141,143,144))

    def test_empty_source_row_does_not_count(self):
        r=execute(ids=(141,142,143),empty=(143,))
        self.assertEqual(r['indexed_row_census']['empty_rows'],1)
        self.assertEqual(r['independent_three_section_gate'],'INSUFFICIENT_CONTROLS')

    def test_deduplicates_identical_suffixes(self):
        r=execute(ids=(141,142,143,144),duplicates=(143,144))
        self.assertEqual(r['byte_identical_postscene_suffix_extra_occurrences'],1)
        self.assertEqual(r['independent_distinct_suffix_section_ids'],[141,142,143])
        self.assertEqual(r['strictly_authenticated_section_ids'],[141,142,143,144])

    def test_three_distinct_sections_but_only_two_unique_tails(self):
        # 141 and 143 share identical group words, but have distinct local hash sets.
        r=execute(ids=(141,142,143), hashes={141:0xA001008D,142:0xA001008E,
                                             143:0xA001008D})
        self.assertEqual(r['byte_identical_postscene_suffix_extra_occurrences'],1)
        self.assertEqual(r['independent_three_section_gate'],'INSUFFICIENT_CONTROLS')

    def test_prefer_known_baseline_on_identical_suffix(self):
        # 100 and 141 duplicate; 141 should stay because it is a known control.
        r=execute(ids=(100,141,142,143),hashes={100:0xA001008D, 141:0xA001008D})
        self.assertIn(141,r['independent_distinct_suffix_section_ids'])
        self.assertNotIn(100,r['independent_distinct_suffix_section_ids'])

    def test_failed_structural_parser_not_treated_as_negative_reference(self):
        r=execute(ids=(141,142,143), malformed=(143,))
        self.assertEqual(r['v3_strict_screen']['independent_sections'],2)
        self.assertEqual(r['indexed_row_census']['strictly_authenticated_rows'],2)

    def test_excessive_eligible_controls_rejected_without_truncation(self):
        ids=tuple([141,142]+list(range(300,400)))
        with self.assertRaisesRegex(ValueError,'More authenticated'):
            execute(ids=ids)

    def test_total_row_limit_checked_before_stream_scan(self):
        with TemporaryDirectory() as d:
            p=Path(d); bun=p/'b'; stream=p/'s';bun.write_bytes(b'x');stream.write_bytes(b'xyz')
            many = {141:(0,1),142:(2048,1)}
            many.update({10000+i:(0,0) for i in range(gate.MAX_INDEX_ROWS)})
            with patch.dict(sys.modules, {'carbon_pc_native_postscene_layout_gate':
                                          SimpleNamespace(stream_rows=lambda a,b: many)}):
                with self.assertRaisesRegex(ValueError,'too many candidate rows'):
                    gate.inspect_originals(bun,stream)

    def test_no_hash_or_stream_offset_leaks(self):
        r=execute()
        text=json.dumps(r)
        for hidden in (str(0xA001008D),str(0xA001008E),str(0xA001008F)):
            self.assertNotIn(hidden,text)
        self.assertNotIn('2048',text)

    def test_malformed_non_value_error_propagates(self):
        with self.assertRaisesRegex(RuntimeError,'parser bug'):
            execute(ids=(141,142,999))


class InputRejectionTests(unittest.TestCase):
    def test_missing_paths(self):
        with self.assertRaisesRegex(ValueError,'regular files'):
            gate.inspect_originals('/no/such/file','/no/such/other')

    def test_alias_inputs(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'file';p.write_bytes(b'abc')
            with self.assertRaisesRegex(ValueError,'alias'):
                gate.inspect_originals(p,p)

    def test_symlink_inputs(self):
        with TemporaryDirectory() as d:
            real=Path(d)/'real';sym=Path(d)/'link';real.write_bytes(b'x');sym.symlink_to(real)
            with self.assertRaisesRegex(ValueError,'regular files'):
                gate.inspect_originals(sym,real)

    def test_duplicate_baselines(self):
        with TemporaryDirectory() as d:
            b=Path(d)/'b';s=Path(d)/'s';b.write_bytes(b'a');s.write_bytes(b'b')
            with self.assertRaisesRegex(ValueError,'Invalid baseline'):
                gate.inspect_originals(b,s,(141,141))

    def test_invalid_baseline_type(self):
        with TemporaryDirectory() as d:
            b=Path(d)/'b';s=Path(d)/'s';b.write_bytes(b'a');s.write_bytes(b'b')
            with self.assertRaisesRegex(ValueError,'Invalid baseline'):
                gate.inspect_originals(b,s,(141,'142'))

    def test_invalid_baseline_range(self):
        with TemporaryDirectory() as d:
            b=Path(d)/'b';s=Path(d)/'s';b.write_bytes(b'a');s.write_bytes(b'b')
            with self.assertRaisesRegex(ValueError,'Invalid baseline'):
                gate.inspect_originals(b,s,(141,999999))


if __name__ == '__main__': unittest.main()
