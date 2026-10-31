"""V62 tests: synthetic chunk streams and metadata-only V61 JSON."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v61'))
import v62_framing_conflict_gate as v62
import v61_carbon_chunk_probe as v61


def frame(tag,payload,order='little',mode='payload'):
    n=len(payload)+(8 if mode=='total' else 0)
    return struct.pack(v61.ENDIAN[order]+'II',tag,n)+payload


def inspect(td, payload, *, modes=('payload',), guard=True, orders=('little',)):
    path=Path(td)/'private_game_archive.bin'
    path.write_bytes(payload)
    return v61.scan_archive(path,orders=orders,modes=modes,
            expected_sha256=hashlib.sha256(payload).hexdigest() if guard else None)


class OverlapGateTests(unittest.TestCase):

    def test_separate_root_and_master_dont_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.ROOT,frame(0x34101,b'abcdef'))+b'SEPARATE'+frame(v61.MASTER,bytes(32))
            result=v62.analyze(inspect(td,raw))
            self.assertEqual(result['candidate_variants_total'],2)
            self.assertEqual(result['master_variants_starting_inside_candidate_ROOTs'],0)
            self.assertEqual(result['candidate_variants_overlapping_another_variant'],0)
            master=next(x for x in result['candidates'] if x['tag']==v62.MASTER)
            self.assertEqual(master['candidate_category'],'master_candidate_without_detected_span_overlap')
            self.assertFalse(result['Carbon_PC_master_layout_verified'])

    def test_master_signature_inside_root(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.ROOT,frame(v61.MASTER,bytes(32)))
            report=v62.analyze(inspect(td,raw))
            self.assertEqual(report['master_variants_starting_inside_candidate_ROOTs'],1)
            self.assertEqual(report['master_variants_wholly_inside_candidate_ROOTs'],1)
            master=next(x for x in report['candidates'] if x['tag']==v62.MASTER)
            root=next(x for x in report['candidates'] if x['tag']==v62.ROOT)
            self.assertTrue(master['master_signature_starts_inside_candidate_root'])
            self.assertEqual(master['candidate_category'],'master_signature_inside_candidate_root')
            self.assertEqual(root['master_signature_offsets_inside_this_root'],1)

    def test_master_signature_inside_root_but_outlasting_short_interpretation(self):
        with tempfile.TemporaryDirectory() as td:
            # Header total-length mode ends eight bytes before payload-length mode.
            raw=frame(v61.ROOT,frame(v61.MASTER,bytes(32)))
            report=v62.analyze(inspect(td,raw,modes=('payload','total')))
            masters=[x for x in report['candidates'] if x['tag']==v62.MASTER]
            self.assertTrue(all(x['master_signature_starts_inside_candidate_root'] for x in masters))
            self.assertTrue(all(x['competing_interpretations_at_same_offset']==1 for x in masters))
            self.assertTrue(report['same_offset_competing_interpretation_locations']>=2)

    def test_nested_root_in_master_payload_is_flagged_as_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.MASTER,frame(v61.ROOT,frame(0x34101,b'content')))
            report=v62.analyze(inspect(td,raw))
            master=next(x for x in report['candidates'] if x['tag']==v62.MASTER)
            self.assertTrue(master['overlap_with_any_other_candidate_variant'])
            self.assertEqual(master['candidate_category'],'master_candidate_with_other_framing_overlap')

    def test_back_to_back_chunks_no_false_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.MASTER,b'Y'*16)+frame(v61.MASTER,b'Z'*16)
            report=v62.analyze(inspect(td,raw))
            self.assertEqual(report['candidate_variants_overlapping_another_variant'],0)

    def test_payload_vs_total_mode_ambiguous_at_same_offset(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.MASTER,b'Y'*64)
            report=v62.analyze(inspect(td,raw,modes=('payload','total')))
            self.assertEqual(report['candidate_variants_total'],2)
            self.assertEqual(report['same_offset_competing_interpretation_locations'],1)
            self.assertEqual(report['candidate_variants_overlapping_another_variant'],2)
            self.assertTrue(all(x['competing_interpretations_at_same_offset']==1 for x in report['candidates']))

    def test_root_contiguous_children_status_retained(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.ROOT,frame(0x34101,b'ABCD'))
            result=v62.analyze(inspect(td,raw))
            root=result['candidates'][0]
            self.assertEqual(root['child_framing_status'],'contiguous_candidate_children')
            self.assertEqual(root['candidate_category'],'root_with_contiguous_candidate_child_frames')

    def test_root_without_children_not_rejected_as_other_platform(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.ROOT,b'opaque PC-like data')
            result=v62.analyze(inspect(td,raw))
            self.assertEqual(result['candidates'][0]['child_framing_status'],'unparsed')
            self.assertFalse(result['independent_original_game_source_authenticated'])

    def test_unguarded_archive_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)),guard=False)
            with self.assertRaisesRegex(v62.ConflictError,'unguarded'):
                v62.analyze(x)

    def test_unguarded_explicit_opt_in_still_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)),guard=False)
            r=v62.analyze(x,require_guard=False)
            self.assertFalse(r['source_expected_digest_guard_applied'])
            self.assertFalse(r['Carbon_PC_loader_or_relocations_verified'])

    def test_missing_new_v61_fields_rejects_stale_report(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            del x['candidates'][0]['framed_chunk_sha256']
            with self.assertRaisesRegex(v62.ConflictError,'framed_chunk_sha256'):
                v62.analyze(x)

    def test_wrong_archive_schema_rejected(self):
        with self.assertRaisesRegex(v62.ConflictError,'schema'):
            v62.analyze({'schema':'old'})

    def test_invalid_end_offset_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            x['candidates'][0]['end_offset_exclusive']+=1
            with self.assertRaisesRegex(v62.ConflictError,'range'):
                v62.analyze(x)

    def test_invalid_archive_size_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            x['archive_size_bytes']-=1
            with self.assertRaisesRegex(v62.ConflictError,'outside archive'):
                v62.analyze(x)

    def test_boolean_offset_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            x['candidates'][0]['offset']=True
            with self.assertRaisesRegex(v62.ConflictError,'offset'):
                v62.analyze(x)

    def test_duplicate_candidate_variant_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            x['candidates'].append(copy.deepcopy(x['candidates'][0]))
            x['candidate_variants']=2
            with self.assertRaisesRegex(v62.ConflictError,'duplicate candidate'):
                v62.analyze(x)

    def test_conflicting_hash_for_same_span_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(64)),modes=('payload','total'))
            # Force the alternate framing to claim the same span but a
            # different hash; V62 must fail rather than average results.
            x['candidates'][1]['total_bytes']=x['candidates'][0]['total_bytes']
            x['candidates'][1]['end_offset_exclusive']=x['candidates'][0]['end_offset_exclusive']
            with self.assertRaisesRegex(v62.ConflictError,'conflicting SHA'):
                v62.analyze(x)

    def test_invalid_digest_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,frame(v61.MASTER,bytes(32)))
            x['candidates'][0]['framed_chunk_sha256']='not-a-hash'
            with self.assertRaisesRegex(v62.ConflictError,'framed_chunk_sha256'):
                v62.analyze(x)

    def test_empty_source_still_valid_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            x=inspect(td,b'')
            r=v62.analyze(x)
            self.assertEqual(r['candidate_variants_total'],0)
            self.assertEqual(r['candidates'],[])
            self.assertFalse(r['safe_to_install'])

    def test_unframed_signature_not_fake_master_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            raw=struct.pack('<II',v61.MASTER,0xFFFFFF00)+b'short'
            x=inspect(td,raw)
            r=v62.analyze(x)
            self.assertEqual(r['candidate_variants_total'],0)

    def test_top_truncation_preserves_total_counts(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.MASTER,b'a'*32)+frame(v61.MASTER,b'b'*32)
            r=v62.analyze(inspect(td,raw),top=1)
            self.assertEqual(r['candidate_variants_total'],2)
            self.assertEqual(r['entries_emitted'],1)
            self.assertTrue(r['entries_truncated'])

    def test_no_user_paths_or_original_payload_bytes_in_report(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.ROOT,frame(0x34101,b'PRIVATE ORIGINAL CONTENT'))
            data=inspect(td,raw)
            r=v62.analyze(data)
            dump=json.dumps(r)
            self.assertNotIn(str(td),dump)
            self.assertNotIn('PRIVATE ORIGINAL CONTENT',dump)
            self.assertNotIn('private_game_archive.bin',dump)

    def test_cli_success_and_no_input_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            report=inspect(td,frame(v61.MASTER,b'content'))
            input_json=Path(td)/'v61.json';output=Path(td)/'v62.json'
            input_json.write_text(json.dumps(report))
            cmd=[sys.executable,str(Path(v62.__file__)),
                 '--v61-report',str(input_json),'--report',str(output)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(output.read_text())['candidate_variants_total'],1)
            self.assertEqual(json.loads(input_json.read_text()),report)
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)

    def test_cli_refuses_self_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            report=inspect(td,frame(v61.MASTER,b'abc'))
            p=Path(td)/'report.json';p.write_text(json.dumps(report))
            cmd=[sys.executable,str(Path(v62.__file__)),
                 '--v61-report',str(p),'--report',str(p)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('refusing overwrite',run.stderr)
            self.assertEqual(json.loads(p.read_text()),report)

    def test_format_traversal_never_reads_original_game(self):
        with tempfile.TemporaryDirectory() as td:
            raw=frame(v61.MASTER,b'nonpublic game bytes')
            v61report=inspect(td,raw)
            archive=Path(td)/'private_game_archive.bin'
            archive.unlink()
            r=v62.analyze(v61report)
            self.assertEqual(r['candidate_variants_total'],1)

    def test_synthetic_many_disjoint_entries_linear(self):
        with tempfile.TemporaryDirectory() as td:
            raw=b''.join(frame(v61.MASTER,bytes(16)) for _ in range(150))
            r=v62.analyze(inspect(td,raw))
            self.assertEqual(r['candidate_variants_overlapping_another_variant'],0)
            self.assertEqual(r['candidate_variants_total'],150)


if __name__=='__main__':
    unittest.main()
