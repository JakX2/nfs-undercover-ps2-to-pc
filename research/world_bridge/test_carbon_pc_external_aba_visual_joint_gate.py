"""Original-free joint A/B/A Carbon I/O and PNG visual evidence regressions."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from carbon_pc_external_aba_visual_joint_gate import (
    audit_owner_aba_joint_files, join_carbon_aba_io_and_visual,
)
from carbon_pc_private_visual_evidence_gate import (
    ROI_FORMAT, compare_png_evidence,
)
from test_carbon_pc_private_visual_evidence_gate import synth_png, paint
from test_carbon_pc_external_aba_capture_gate import (
    audit as make_io, baseline, controlled, restored,
)
from test_carbon_pc_original_loader_control_chain import (
    MANIFEST, SOURCE, WINDOWS_GAME,
)


class JointEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.before = root / 'baseline.png'
        self.control = root / 'control.png'
        self.restore = root / 'restore.png'
        self.roi = root / 'roi.json'
        self.w, self.h = 32, 24
        self.target = (9, 5, 10, 10)
        self.orig = bytes((20, 24, 28)) * (self.w * self.h)
        self.before.write_bytes(synth_png(self.w, self.h, self.orig))
        self.control.write_bytes(synth_png(self.w, self.h,
            paint(self.w, self.h, self.target)))
        self.restore.write_bytes(synth_png(self.w, self.h, self.orig))
        self.roi.write_text(json.dumps({
            'format': ROI_FORMAT,
            'target': list(self.target),
            'anchors': [[0, 0, 5, 5], [27, 19, 5, 5]]
        }), encoding='utf-8')

    def visual(self):
        return compare_png_evidence(
            self.before, self.control, self.roi, self.restore)

    def join(self, io=None):
        return join_carbon_aba_io_and_visual(
            make_io() if io is None else io, self.visual())

    def test_full_file_and_reversible_localized_visual_are_only_candidates(self):
        r = self.join()
        self.assertEqual(r['joint_evidence_level'],
                         'CORRELATED_FILE_READ_AND_REVERSIBLE_SCREEN_CANDIDATE_NOT_REGISTRATION')
        self.assertTrue(r['external_read_isolated_to_control'])
        self.assertTrue(r['external_full_file_read_observed'])
        self.assertTrue(r['reversible_localized_screen_change_candidate'])
        self.assertTrue(r['screen_target_reverted_to_baseline'])
        self.assertTrue(r['background_anchors_stable'])
        for flag in ('test_run_order_verified',
                     'snapshot_to_procmon_time_alignment_verified',
                     'loader_asi_executed_verified',
                     'engine_resource_registration_verified',
                     'specific_undercover_asset_rendering_verified',
                     'carbon_gameplay_port_verified', 'files_modified'):
            self.assertFalse(r[flag])

    def test_visual_change_without_control_file_read_not_joint_evidence(self):
        io = make_io(control=baseline())
        r = self.join(io)
        self.assertEqual(r['joint_evidence_level'],
                         'REVERSIBLE_VISUAL_CANDIDATE_WITHOUT_ISOLATED_FILE_READ')
        self.assertFalse(r['external_read_isolated_to_control'])

    def test_file_read_without_visual_change_is_not_joint_evidence(self):
        self.control.write_bytes(synth_png(self.w, self.h, self.orig))
        r = self.join()
        self.assertEqual(r['joint_evidence_level'],
                         'ISOLATED_FILE_READ_WITHOUT_REVERSIBLE_VISUAL_CANDIDATE')
        self.assertFalse(r['reversible_localized_screen_change_candidate'])

    def test_background_motion_prevents_joint_evidence(self):
        self.control.write_bytes(synth_png(
            self.w, self.h, bytes((100, 80, 60)) * (self.w * self.h)))
        r = self.join()
        self.assertFalse(r['background_anchors_stable'])
        self.assertFalse(r['reversible_localized_screen_change_candidate'])

    def test_failed_restore_prevents_joint_evidence(self):
        self.restore.write_bytes(self.control.read_bytes())
        r = self.join()
        self.assertFalse(r['screen_target_reverted_to_baseline'])
        self.assertFalse(r['reversible_localized_screen_change_candidate'])

    def test_uncalibrated_capture_is_not_joint_evidence(self):
        io = make_io(base=controlled())
        # Control external access during BASELINE makes it non-isolated.
        self.assertFalse(io['external_access_isolated_to_control_capture'])
        self.assertFalse(self.join(io)['external_read_isolated_to_control'])
        from test_carbon_pc_external_aba_capture_gate import csv_log
        io2 = make_io(base=csv_log())
        self.assertFalse(io2['all_captures_calibrated'])
        self.assertFalse(self.join(io2)['external_read_isolated_to_control'])

    def test_corrupt_or_forged_report_structure_rejected(self):
        io = make_io()
        visual = self.visual()
        for corrupted in (
            None,
            {'scope': io['scope'], 'all_captures_calibrated': 'yes'},
            {**io, 'scope': 'INVALID'},
            {**io, 'control_same_pid_open_read_observed': 1},
        ):
            with self.subTest(corrupted=str(corrupted)[:30]):
                with self.assertRaises(ValueError):
                    join_carbon_aba_io_and_visual(corrupted, visual)
        for corrupted in (
            None, {'scope': visual['scope']},
            {**visual, 'scope': 'DIFFERENT'},
            {**visual, 'restoration_control_performed': 'true'},
        ):
            with self.subTest(corrupted=str(corrupted)[:30]):
                with self.assertRaises(ValueError):
                    join_carbon_aba_io_and_visual(io, corrupted)

    def test_private_paths_and_roi_coordinates_not_in_output(self):
        result = json.dumps(self.join())
        for private in (
            str(self.before), str(self.control), str(self.roi),
            WINDOWS_GAME, '0xA0B0C0D0', str(self.target)
        ):
            self.assertNotIn(private, result)


class OwnerPrivateJointTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        self.game = root / 'Carbon'
        (self.game / 'scripts').mkdir(parents=True)
        (self.game / 'MODS').mkdir()
        (self.game / 'TRACKS').mkdir()
        self.manifest = self.game / 'scripts' / 'XNFSModFiles.txt'
        self.external = self.game / 'MODS' / 'KnownGoodPC.BUN'
        self.sentinel = self.game / 'TRACKS' / 'STREAML5RB.BUN'
        self.csv_a = root / 'baseline.csv'
        self.csv_b = root / 'control.csv'
        self.csv_r = root / 'restore.csv'
        self.png_a = root / 'baseline.png'
        self.png_b = root / 'control.png'
        self.png_r = root / 'restore.png'
        self.roi = root / 'roi.json'
        self.manifest.write_bytes(MANIFEST)
        self.external.write_bytes(SOURCE)
        self.sentinel.write_bytes(b'SYNTHETIC ORIGINAL STOCK')
        self.csv_a.write_text(baseline(), encoding='utf-8')
        self.csv_b.write_text(controlled(), encoding='utf-8')
        self.csv_r.write_text(restored(), encoding='utf-8')
        base = bytes((20, 24, 28)) * (32 * 24)
        self.png_a.write_bytes(synth_png(32, 24, base))
        self.png_b.write_bytes(synth_png(32, 24, paint(32, 24, (9, 5, 10, 10))))
        self.png_r.write_bytes(synth_png(32, 24, base))
        self.roi.write_text(json.dumps({
            'format': ROI_FORMAT, 'target': [9, 5, 10, 10],
            'anchors': [[0, 0, 5, 5], [27, 19, 5, 5]]
        }), encoding='utf-8')

    def audited(self, **changes):
        args = {
            'game_directory': self.game, 'manifest_path': self.manifest,
            'original_resource_path': self.external,
            'sentinel_game_file': self.sentinel,
            'baseline_csv': self.csv_a, 'control_csv': self.csv_b,
            'restore_csv': self.csv_r, 'kind': 'geometry',
            'baseline_png': self.png_a, 'control_png': self.png_b,
            'restore_png': self.png_r, 'roi_json': self.roi,
            'windows_root_override_for_tests': WINDOWS_GAME,
        }
        args.update(changes)
        return audit_owner_aba_joint_files(**args)

    def test_all_private_sources_unchanged(self):
        inputs = (
            self.manifest, self.external, self.sentinel,
            self.csv_a, self.csv_b, self.csv_r,
            self.png_a, self.png_b, self.png_r, self.roi)
        before = tuple((p.read_bytes(), p.stat().st_mtime_ns) for p in inputs)
        result = self.audited()
        after = tuple((p.read_bytes(), p.stat().st_mtime_ns) for p in inputs)
        self.assertEqual(before, after)
        self.assertEqual(result['joint_evidence_level'],
                         'CORRELATED_FILE_READ_AND_REVERSIBLE_SCREEN_CANDIDATE_NOT_REGISTRATION')
        self.assertFalse(result['files_modified'])

    def test_missing_restored_screenshot_fails(self):
        self.png_r.unlink()
        with self.assertRaises(ValueError):
            self.audited()

    def test_reuses_private_file_path_rejected(self):
        with self.assertRaises(ValueError):
            self.audited(restore_png=self.png_a)
        with self.assertRaises(ValueError):
            self.audited(roi_json=self.csv_a)

    def test_hardlinked_png_rejected(self):
        alias = self.png_a.parent / 'hardlink.png'
        try:
            os.link(self.png_a, alias)
        except (OSError, NotImplementedError):
            self.skipTest('Hardlinks not supported')
        with self.assertRaises(ValueError):
            self.audited(restore_png=alias)

    def test_symlinked_png_rejected(self):
        alias = self.png_a.parent / 'alias.png'
        try:
            alias.symlink_to(self.png_a)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):
            self.audited(restore_png=alias)

    def test_invalid_png_fails_closed(self):
        self.png_b.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            self.audited()

    def test_failed_existing_aba_chain_blocks_joint_report(self):
        self.csv_b.write_text(baseline(), encoding='utf-8')
        result = self.audited()
        self.assertEqual(result['joint_evidence_level'],
                         'REVERSIBLE_VISUAL_CANDIDATE_WITHOUT_ISOLATED_FILE_READ')
        self.assertFalse(result['external_read_isolated_to_control'])

    def test_rejects_png_mutation_during_comparison(self):
        # Underlying comparator is mocked solely to simulate an outside
        # process changing PNG bytes during the read-only audit.
        import carbon_pc_external_aba_visual_joint_gate as module
        original = module.compare_png_evidence
        def mutate(*args):
            result = original(*args)
            self.png_b.write_bytes(self.png_b.read_bytes() + b'extra')
            return result
        with patch.object(module, 'compare_png_evidence', mutate):
            with self.assertRaises(ValueError):
                self.audited()


if __name__ == '__main__':
    unittest.main()
