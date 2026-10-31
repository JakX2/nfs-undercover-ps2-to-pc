"""V60 tests: synthetic V58 archive reports only; no original game assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v58'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v56'))
import v60_candidate_cohorts as v60
import v58_stream_scene_bridge as v58
from test_v56 import fixture,replace_tree_payload,chain_tree


def scanned(tmp, raw, *, hint='wii', guard=True, filename='archive.bin'):
    path=Path(tmp)/filename
    path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest()
    return v58.scan_archive(path,source_hint=hint,
                            expected_stream_sha256=digest if guard else None)


def instance_only_fixture():
    # Two AABB-consistent tree nodes; 3 instance rows; 3 preculler blocks.
    # 3*128=(3+1)*96, whereas 2*384 differs.
    tree=bytearray(chain_tree(2))
    struct.pack_into('<H',tree,48+12,3)
    struct.pack_into('<3h',tree,48+28,0,1,2)
    return replace_tree_payload(fixture(n=3,blocks=3),bytes(tree))


class CohortTests(unittest.TestCase):
    def test_original_fixture_not_required(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3,blocks=3))
            x=v60.compare([a])
            self.assertFalse(x['independent_original_Wii_scenes_authenticated'])
            self.assertFalse(x['Carbon_PC_preculler_serialization_proven'])
            self.assertFalse(x['safe_to_install'])

    def test_v58_emits_independent_instance_and_component_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture())
            rec=a['records'][0]
            for field in ('candidate_instance_payload_sha256','candidate_scene_payload_sha256',
                          'candidate_preculler_payload_sha256','candidate_tree_payload_sha256'):
                self.assertEqual(len(rec[field]),64)
            self.assertNotEqual(rec['root_sha256'],rec['candidate_instance_payload_sha256'])

    def test_modified_noninstance_bytes_do_not_count_as_new_instance(self):
        with tempfile.TemporaryDirectory() as td:
            raw=fixture()
            other=raw[:-1]+bytes([raw[-1]^8])
            a=scanned(td,raw,filename='a')
            b=scanned(td,other,filename='b')
            x=v60.compare([a,b])
            self.assertEqual(x['distinct_candidate_ROOT_sha256s'],2)
            self.assertEqual(x['distinct_consistent_Wii_instance_payload_sha256s'],1)
            self.assertEqual(x['same_instance_different_ROOT_groups'],1)
            self.assertEqual(x['priority_candidates'][0]['same_instance_distinct_ROOT_count'],2)

    def test_repeated_identical_ROOT_not_independent(self):
        with tempfile.TemporaryDirectory() as td:
            raw=fixture()
            report=scanned(td,raw+b'gap'+raw)
            x=v60.compare([report])
            self.assertEqual(x['total_candidate_ROOT_occurrences'],2)
            self.assertEqual(x['exact_ROOT_duplicate_occurrences'],1)
            self.assertEqual(x['distinct_candidate_ROOT_sha256s'],1)

    def test_cross_archive_same_root_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(),filename='a')
            b=scanned(td,fixture(),filename='b')
            x=v60.compare([a,b])
            self.assertEqual(x['distinct_archive_sha256s'],1)
            self.assertEqual(x['exact_ROOT_duplicate_occurrences'],1)
            self.assertEqual(x['priority_candidates'][0]['occurrences_of_representative_ROOT'],2)

    def test_two_distinct_instance_payloads_no_original_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3),filename='a')
            b=scanned(td,fixture(n=4),filename='b')
            x=v60.compare([a,b])
            self.assertEqual(x['distinct_consistent_Wii_instance_payload_sha256s'],2)
            self.assertFalse(x['independent_original_Wii_scenes_authenticated'])

    def test_both_hypotheses(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3,blocks=3))
            x=v60.compare([a])
            self.assertEqual(x['priority_candidates'][0]['hypothesis_pattern'],'both_hypotheses')

    def test_tree_only_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=4,blocks=3))
            x=v60.compare([a])
            self.assertEqual(x['priority_candidates'][0]['hypothesis_pattern'],'tree_count_only')

    def test_instance_only_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,instance_only_fixture())
            self.assertEqual(a['records'][0]['candidate_wii_graph_status'],'candidate_internally_consistent')
            x=v60.compare([a])
            self.assertEqual(x['priority_candidates'][0]['hypothesis_pattern'],'instance_count_only')

    def test_neither_hypothesis_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3,blocks=6))
            x=v60.compare([a])
            self.assertEqual(x['priority_candidates'][0]['hypothesis_pattern'],'neither_hypothesis')

    def test_discriminating_candidate_prioritized_over_both(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3,blocks=3)+fixture(n=4,blocks=3))
            x=v60.compare([a])
            self.assertEqual(x['priority_candidates'][0]['hypothesis_pattern'],'tree_count_only')

    def test_rejected_graph_never_proves_numerical_discriminator(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(bad_prec=77))
            x=v60.compare([a])
            self.assertEqual(x['consistent_candidate_Wii_ROOT_sha256s'],0)
            self.assertEqual(x['priority_candidates'],[])

    def test_pc_hint_never_inferred_wii_abi(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(),hint='carbon_pc')
            x=v60.compare([a])
            self.assertEqual(x['consistent_candidate_Wii_ROOT_sha256s'],0)
            self.assertFalse(x['Carbon_PC_preculler_serialization_proven'])

    def test_unguarded_input_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(),guard=False)
            with self.assertRaisesRegex(v60.CohortError,'unguarded'):
                v60.compare([a])

    def test_unguarded_opt_in_labeled(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(),guard=False)
            x=v60.compare([a],require_guard=False)
            self.assertEqual(x['unguarded_inventory_reports'],1)
            self.assertFalse(x['independent_original_Wii_scenes_authenticated'])

    def test_old_v58_inventory_requires_regeneration(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture())
            del a['records'][0]['candidate_instance_payload_sha256']
            with self.assertRaisesRegex(v60.CohortError,'candidate_instance_payload_sha256'):
                v60.compare([a])

    def test_bad_root_occurrence_count_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture());a['candidate_root_occurrences']+=1
            with self.assertRaisesRegex(v60.CohortError,'occurrence count'):
                v60.compare([a])

    def test_contradictory_root_hash_record_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture())
            b=scanned(td,fixture(n=4))
            b['records'][0]['root_sha256']=a['records'][0]['root_sha256']
            with self.assertRaisesRegex(v60.CohortError,'conflicting metadata'):
                v60.compare([a,b])

    def test_forged_claimed_root_range_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture())
            a['records'][0]['root_bytes']=a['archive_size_bytes']+10
            with self.assertRaisesRegex(v60.CohortError,'range exceeds'):
                v60.compare([a])

    def test_boolean_counts_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture())
            a['records'][0]['candidate_instance_count']=True
            with self.assertRaisesRegex(v60.CohortError,'candidate counts'):
                v60.compare([a])

    def test_report_no_private_source_path(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(),filename='VERY_PRIVATE_GAME_SOURCE.BUN')
            x=v60.compare([a])
            encoded=json.dumps(x)
            self.assertNotIn('VERY_PRIVATE_GAME_SOURCE',encoded)
            self.assertNotIn(str(td),encoded)
            self.assertTrue(x['read_only'])

    def test_top_limits_and_truncation(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,fixture(n=3)+fixture(n=4))
            x=v60.compare([a],top=1)
            self.assertEqual(len(x['priority_candidates']),1)
            self.assertTrue(x['priority_entries_truncated'])
            self.assertEqual(x['priority_count_total'],2)

    def test_empty_archive_inventory_valid(self):
        with tempfile.TemporaryDirectory() as td:
            a=scanned(td,b'')
            x=v60.compare([a])
            self.assertEqual(x['total_candidate_ROOT_occurrences'],0)
            self.assertEqual(x['priority_candidates'],[])

    def test_cli_preserves_input_reports_and_refuses_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            report=scanned(td,fixture())
            p=Path(td)/'input.json';p.write_text(json.dumps(report))
            output=Path(td)/'summary.json'
            cmd=[sys.executable,str(Path(v60.__file__)),
                 '--inventory',str(p),'--report',str(output)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            before=p.read_text()
            self.assertEqual(json.loads(output.read_text())['priority_count_total'],1)
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual(p.read_text(),before)

    def test_cli_rejects_self_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            report=scanned(td,fixture())
            p=Path(td)/'input.json';p.write_text(json.dumps(report))
            cmd=[sys.executable,str(Path(v60.__file__)),
                 '--inventory',str(p),'--report',str(p)]
            r=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(json.loads(p.read_text()),report)


if __name__=='__main__':
    unittest.main()
