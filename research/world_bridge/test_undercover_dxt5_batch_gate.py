"""Synthetic, source-free regression controls for bounded Undercover DXT5 audits."""
import copy
import unittest
from unittest.mock import patch

import undercover_dxt5_batch_gate as gate


def _source(ordinal):
    if ordinal not in range(4):
        raise ValueError('Unexpected source ordinal')
    width, height = 4, 4
    rgba = bytearray()
    for pixel in range(16):
        rgba.extend(((ordinal * 41 + pixel * 9) & 255,
                     (pixel * 31 + 4) & 255, ordinal * 23,
                     (128 + pixel) if ordinal % 2 else 255))
    return bytes(rgba),width,height,(4 if ordinal < 2 else 8),(ordinal % 2)


def _make():
    with patch.object(gate, 'parse_pack',return_value={'records':{x:None for x in range(4)}}),\
         patch.object(gate,'decode_undercover_source',side_effect=lambda _s,i:_source(i)):
        return gate.audit_section_range(b'SYNTHETIC-ONLY-SECTION',241,0,2),\
               gate.audit_section_range(b'SYNTHETIC-ONLY-SECTION',241,2,2),\
               gate.audit_section_range(b'SYNTHETIC-ONLY-SECTION',241,0,4)


class BatchAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first,cls.second,cls.whole = _make()

    def test_full_batch_and_merged_statistics_are_equivalent(self):
        split = gate.combine_batches([self.first,self.second])
        whole = gate.combine_batches([self.whole])
        self.assertEqual(split,whole)
        self.assertEqual(split['original_textures_covered'],4)

    def test_batches_accept_reverse_order(self):
        self.assertEqual(gate.combine_batches([self.second,self.first]),
                         gate.combine_batches([self.first,self.second]))

    def test_fingerprint_is_private_in_final_summary(self):
        self.assertIn('private_source_sha256',self.first)
        self.assertNotIn('private_source_sha256',gate.combine_batches([self.first,self.second]))

    def test_no_original_names_or_hashes_in_report(self):
        s = str(gate.combine_batches([self.first,self.second]))
        self.assertNotIn('texture_hash',s)
        self.assertNotIn('texture_name',s)

    def test_empty_batch_list_rejected(self):
        with self.assertRaisesRegex(ValueError,'No batch'):
            gate.combine_batches([])

    def test_overlapping_ranges_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):
            gate.combine_batches([self.first,self.first,self.second])

    def test_incomplete_ranges_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            gate.combine_batches([self.first])

    def test_gap_rejected(self):
        bad=copy.deepcopy(self.second);bad['range_start']=3
        with self.assertRaisesRegex(ValueError,'Missing'):
            gate.combine_batches([self.first,bad])

    def test_wrong_source_fingerprint_rejected(self):
        bad=copy.deepcopy(self.second);bad['private_source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Mixed'):
            gate.combine_batches([self.first,bad])

    def test_malformed_fingerprint_rejected(self):
        bad=copy.deepcopy(self.whole);bad['private_source_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            gate.combine_batches([bad])

    def test_cross_section_mixing_rejected(self):
        bad=copy.deepcopy(self.second);bad['section_id']=3401
        with self.assertRaisesRegex(ValueError,'Mixed'):
            gate.combine_batches([self.first,bad])

    def test_wrong_codec_count_rejected(self):
        bad=copy.deepcopy(self.whole);bad['data']['textures']+=1
        with self.assertRaisesRegex(ValueError,'count'):
            gate.combine_batches([bad])

    def test_aggregate_depth_mismatch_rejected(self):
        bad=copy.deepcopy(self.whole);bad['indexed_depths']['4']['pixels']+=1
        with self.assertRaisesRegex(ValueError,'reconcile'):
            gate.combine_batches([bad])

    def test_aggregate_depth_metric_mismatch_rejected(self):
        bad=copy.deepcopy(self.whole);bad['indexed_depths']['4']['texture_rgb_mae_sum']+=0.5
        with self.assertRaisesRegex(ValueError,'reconcile'):
            gate.combine_batches([bad])

    def test_swizzle_flag_count_rejected(self):
        bad=copy.deepcopy(self.whole);bad['swizzle_flags']['1']+=1
        with self.assertRaisesRegex(ValueError,'reconcile'):
            gate.combine_batches([bad])

    def test_invalid_boolean_swizzle_count_rejected(self):
        bad=copy.deepcopy(self.whole);bad['swizzle_flags']['0']=False
        with self.assertRaisesRegex(ValueError,'integer'):
            gate.combine_batches([bad])

    def test_unsafe_pixel_sum_rejected(self):
        bad=copy.deepcopy(self.whole);bad['data']['alpha_absolute_sum']=10000000
        with self.assertRaisesRegex(ValueError,'Impossible'):
            gate.combine_batches([bad])

    def test_source_nonopaque_pixel_count_rejected(self):
        bad=copy.deepcopy(self.whole);bad['nonopaque_pixels']=bad['data']['pixels']+1
        with self.assertRaisesRegex(ValueError,'alpha coverage'):
            gate.combine_batches([bad])

    def test_bad_schema_rejected(self):
        bad=copy.deepcopy(self.whole);bad['schema']='other'
        with self.assertRaisesRegex(ValueError,'Mixed'):
            gate.combine_batches([bad])

    def test_invalid_run_limit_rejected(self):
        with self.assertRaisesRegex(ValueError,'Batch exceeds'):
            gate.audit_section_range(b'x',241,0,gate.MAX_BATCH+1)

    def test_invalid_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            gate.audit_section_range(b'x',242,0,1)

    def test_boolean_start_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid integer'):
            gate.audit_section_range(b'x',241,True,1)

    def test_zero_count_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid integer'):
            gate.audit_section_range(b'x',241,0,0)

    def test_out_of_bounds_range_rejected(self):
        with patch.object(gate,'parse_pack',return_value={'records':{0:None}}):
            with self.assertRaisesRegex(ValueError,'outside'):
                gate.audit_section_range(b'x',241,1,1)

    def test_bad_decoded_rgba_length_rejected(self):
        with patch.object(gate,'parse_pack',return_value={'records':{0:None}}),\
             patch.object(gate,'decode_undercover_source',return_value=(b'x',4,4,4,1)):
            with self.assertRaisesRegex(ValueError,'RGBA byte count'):
                gate.audit_section_range(b'x',241,0,1)


if __name__=='__main__':
    unittest.main()
