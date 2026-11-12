"""No game assets, installation files, or real Carbon process needed."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import carbon_pc_private_smoke_session as gate


class SmokeSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'game' / 'TRACKS').mkdir(parents=True)
        self.clean = self.root / 'pristine.bun'
        self.staged = self.root / 'staged.bun'
        self.installed = self.root / 'game' / 'TRACKS' / 'STREAML5RB.BUN'
        self.bundle = self.root / 'L5RB.BUN'
        self.session = self.root / 'private-session'
        self.base = bytes(i % 251 for i in range(4096))
        changed = bytearray(self.base)
        changed[150:190] = bytes((i ^ 0x66) for i in self.base[150:190])
        self.modified = bytes(changed)
        self.clean.write_bytes(self.base)
        self.staged.write_bytes(self.modified)
        self.installed.write_bytes(self.base)
        self.bundle.write_bytes(b'FAKE_SOURCE_BUNDLE')
        self.span = mock.patch.object(gate, '_span', return_value=(128, 96))
        self.span.start()
        self.addCleanup(self.span.stop)

    def _args(self):
        return (self.bundle,self.clean,self.staged,self.installed,141,'DXT5',0)

    def _prepared(self):
        return gate.prepare(self.session, *self._args())

    def _install(self):
        with mock.patch.object(gate, '_require_game_closed'):
            return gate.apply_session(self.session, 'install', confirmed=True, game_closed=True)

    def _restore(self):
        with mock.patch.object(gate, '_require_game_closed'):
            return gate.apply_session(self.session, 'restore', confirmed=True, game_closed=True)

    def test_preflight_is_read_only(self):
        r=gate.preflight(*self._args())
        self.assertEqual(r['changed_bytes'],40)
        self.assertEqual(r['image_length'],96)
        self.assertEqual(self.installed.read_bytes(), self.base)
        self.assertFalse(self.session.exists())

    def test_preflight_private_report_omits_paths_and_digests(self):
        r=gate._public_report('preflight_only_no_files_modified',gate.preflight(*self._args()))
        s=json.dumps(r)
        self.assertNotIn(str(self.root), s)
        self.assertNotIn(gate._digest(self.clean), s)
        self.assertIn('not_rendering',s.lower())

    def test_preflight_rejects_changed_outside_image(self):
        bytes_ = bytearray(self.modified)
        bytes_[11] ^= 1
        self.staged.write_bytes(bytes_)
        with self.assertRaisesRegex(ValueError,'outside'):
            gate.preflight(*self._args())

    def test_preflight_rejects_unmodified_stage(self):
        self.staged.write_bytes(self.base)
        with self.assertRaises(ValueError):
            gate.preflight(*self._args())

    def test_preflight_rejects_wrong_installed(self):
        self.installed.write_bytes(self.modified)
        with self.assertRaisesRegex(ValueError,'pristine'):
            gate.preflight(*self._args())

    def test_preflight_rejects_short_installed(self):
        self.installed.write_bytes(self.base[:-1])
        with self.assertRaisesRegex(ValueError,'size'):
            gate.preflight(*self._args())

    def test_preflight_rejects_wrong_section(self):
        with self.assertRaisesRegex(ValueError,'sections'):
            gate.preflight(*self._args()[:-3],140,'DXT5',0)

    def test_preflight_rejects_wrong_codec(self):
        with self.assertRaisesRegex(ValueError,'codec'):
            gate.preflight(*self._args()[:-2],'DXT7',0)

    def test_preflight_rejects_negative_slot(self):
        with self.assertRaisesRegex(ValueError,'codec/slot'):
            gate.preflight(*self._args()[:-1],-1)

    def test_preflight_rejects_wrong_installed_name(self):
        other = self.root / 'game' / 'TRACKS' / 'fake.bun';other.write_bytes(self.base)
        with self.assertRaisesRegex(ValueError,'TRACKS'):
            gate.preflight(*self._args()[:3],other,141,'DXT5',0)

    def test_preflight_rejects_wrong_installed_directory(self):
        other = self.root / 'STREAML5RB.BUN';other.write_bytes(self.base)
        with self.assertRaisesRegex(ValueError,'TRACKS'):
            gate.preflight(*self._args()[:3],other,141,'DXT5',0)

    def test_preflight_rejects_symlink_file(self):
        link = self.root / 'symlink-stage'
        try:link.symlink_to(self.staged)
        except (OSError,NotImplementedError):self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            gate.preflight(self.bundle,self.clean,link,self.installed,141,'DXT5',0)

    def test_preflight_rejects_symlink_directory(self):
        link = self.root / 'alias'
        try: link.symlink_to(self.root / 'game' / 'TRACKS', target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            gate.preflight(self.bundle,self.clean,self.staged,link/'STREAML5RB.BUN',141,'DXT5',0)

    def test_preflight_rejects_hardlink(self):
        alias = self.root / 'alias.bun'
        try:os.link(self.staged,alias)
        except OSError:self.skipTest('Hardlink unavailable')
        self.installed.unlink()
        os.link(self.clean,self.installed)
        with self.assertRaisesRegex(ValueError,'distinct'):
            gate.preflight(*self._args())

    def test_preflight_rejects_missing_file(self):
        self.bundle.unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):
            gate.preflight(*self._args())

    def test_preflight_rejects_oversized_stream(self):
        with mock.patch.object(gate,'MAX_STREAM',2048):
            with self.assertRaisesRegex(ValueError,'oversized'):
                gate.preflight(*self._args())

    def test_preflight_rejects_invalid_image_span(self):
        with mock.patch.object(gate,'_span',return_value=(4080,96)):
            with self.assertRaisesRegex(ValueError,'bounds'):
                gate.preflight(*self._args())

    def test_prepare_copies_backup_without_touching_installed(self):
        report=self._prepared()
        self.assertEqual(report['state'],'backup_created_no_installation_change')
        self.assertEqual(self.installed.read_bytes(),self.base)
        self.assertEqual((self.session/gate.BACKUP).read_bytes(),self.base)
        self.assertTrue((self.session/gate.MANIFEST).is_file())

    def test_prepare_rejects_session_inside_game_directory(self):
        unsafe = self.root / 'game' / 'private-session'
        with self.assertRaisesRegex(ValueError, 'outside the game'):
            gate.prepare(unsafe, *self._args())
        self.assertFalse(unsafe.exists())
        self.assertEqual(self.installed.read_bytes(), self.base)

    def test_prepare_refuses_existing_session(self):
        self._prepared()
        with self.assertRaises(FileExistsError):
            self._prepared()
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_manifest_has_private_paths_only_on_disk(self):
        report=self._prepared()
        data=json.loads((self.session/gate.MANIFEST).read_text())
        self.assertEqual(data['installed'],str(self.installed))
        self.assertNotIn(str(self.installed),json.dumps(report))

    def test_status_reports_original_before_install(self):
        self._prepared()
        self.assertEqual(gate.status(self.session)['state'],'original_installed')

    def test_install_requires_apply(self):
        self._prepared()
        with self.assertRaisesRegex(ValueError,'apply'):
            gate.apply_session(self.session,'install',confirmed=False)
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_restore_requires_apply(self):
        self._prepared()
        with self.assertRaisesRegex(ValueError,'apply'):
            gate.apply_session(self.session,'restore',confirmed=False)

    def test_install_requires_closed_game(self):
        self._prepared()
        with self.assertRaisesRegex(ValueError,'game-closed|Windows-only'):
            gate.apply_session(self.session,'install',confirmed=True,game_closed=False)
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_install_replaces_only_verified_target(self):
        self._prepared()
        self.assertEqual(self._install()['state'],'stage_installed_not_rendering_proof')
        self.assertEqual(self.installed.read_bytes(),self.modified)
        self.assertEqual(self.clean.read_bytes(),self.base)
        self.assertEqual((self.session/gate.BACKUP).read_bytes(),self.base)
        self.assertEqual(gate.status(self.session)['state'],'stage_installed_not_rendering_proof')

    def test_install_rejects_second_attempt(self):
        self._prepared();self._install()
        with self.assertRaisesRegex(ValueError,'unmodified original'):
            self._install()

    def test_install_rejects_changed_source(self):
        self._prepared()
        self.clean.write_bytes(self.base[:-1]+b'x')
        with self.assertRaisesRegex(ValueError,'source or backup'):
            self._install()
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_install_rejects_changed_stage(self):
        self._prepared()
        self.staged.write_bytes(self.modified[:-1]+b'x')
        with self.assertRaisesRegex(ValueError,'source or backup'):
            self._install()
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_install_rejects_corrupt_backup(self):
        self._prepared()
        (self.session/gate.BACKUP).write_bytes(self.modified)
        with self.assertRaisesRegex(ValueError,'source or backup'):
            self._install()

    def test_install_rejects_concurrent_lock_without_deleting_it(self):
        self._prepared()
        lock=self.session/gate.LOCK
        lock.write_text('another-run')
        with self.assertRaises(FileExistsError):
            self._install()
        self.assertEqual(lock.read_text(),'another-run')
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_restore_verifies_original(self):
        self._prepared();self._install()
        report=self._restore()
        self.assertEqual(report['state'],'restored_original_verified')
        self.assertEqual(self.installed.read_bytes(),self.base)
        self.assertEqual(gate.status(self.session)['state'],'original_installed')

    def test_restore_idempotent(self):
        self._prepared()
        self.assertEqual(self._restore()['state'],'already_original_no_files_modified')
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_restore_rejects_unexpected_installed(self):
        self._prepared();self._install()
        corrupt=bytearray(self.modified);corrupt[40]^=1
        self.installed.write_bytes(corrupt)
        with self.assertRaisesRegex(ValueError,'unexpected'):
            self._restore()
        self.assertEqual(self.installed.read_bytes(),bytes(corrupt))

    def test_status_reports_unknown_without_overwriting(self):
        self._prepared()
        corrupted=bytearray(self.base);corrupted[88]^=1
        self.installed.write_bytes(corrupted)
        self.assertEqual(gate.status(self.session)['state'],'unexpected_installed_bytes_refuse_to_overwrite')

    def test_restore_rejects_missing_backup(self):
        self._prepared();self._install()
        (self.session/gate.BACKUP).unlink()
        with self.assertRaises(ValueError):
            self._restore()

    def test_restore_rejects_corrupt_manifest(self):
        self._prepared();self._install()
        (self.session/gate.MANIFEST).write_text('{broken json')
        with self.assertRaises(json.JSONDecodeError):
            self._restore()

    def test_restore_rejects_tampered_manifest(self):
        self._prepared();self._install()
        path=self.session/gate.MANIFEST
        data=json.loads(path.read_text());data['image_start']=0
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'span changed'):
            self._restore()

    def test_restore_rejects_unrelated_manifest_field(self):
        self._prepared()
        path=self.session/gate.MANIFEST
        data=json.loads(path.read_text());data['arbitrary']='hijacked'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            gate.status(self.session)

    def test_evidence_requires_installed_stage(self):
        self._prepared()
        with self.assertRaisesRegex(ValueError,'stage currently installed'):
            gate.evidence(self.session,self.root/'events.csv')

    def test_evidence_delegates_to_previous_attestor(self):
        import sys
        from types import SimpleNamespace
        self._prepared();self._install()
        temp_module=SimpleNamespace(attest=mock.Mock(return_value={'evidence_level':'synthetic_open_read'}))
        with mock.patch.dict(sys.modules, {'carbon_pc_runtime_span_attestation':temp_module}):
            r=gate.evidence(self.session,self.root/'events.csv')
        self.assertEqual(r['evidence_level'],'synthetic_open_read')
        self.assertEqual(temp_module.attest.call_count,1)

    def test_install_does_not_write_when_game_guard_rejects(self):
        self._prepared()
        with mock.patch.object(gate,'_require_game_closed',side_effect=ValueError('process running')):
            with self.assertRaisesRegex(ValueError,'process running'):
                gate.apply_session(self.session,'install',confirmed=True,game_closed=True)
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_atomic_copy_bad_checksum_does_not_replace(self):
        self._prepared()
        with self.assertRaisesRegex(ValueError,'checksum'):
            gate._atomic_copy_into(self.staged,self.installed,'0'*64)
        self.assertEqual(self.installed.read_bytes(),self.base)

    def test_file_hash_is_private(self):
        self._prepared();r=self._install()
        self.assertNotIn(gate._digest(self.clean),json.dumps(r))
        self.assertNotIn(str(self.root),json.dumps(r))


if __name__ == '__main__':
    unittest.main()
