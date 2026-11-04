"""Source-free end-to-end Undercover donor -> private Carbon DXT5 stream tests."""
import json
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from test_private_undercover_dxt5_archive_audit import fixture as source_fixture
from test_private_undercover_dxt5_archive_audit import bundle
from test_undercover_to_pc_dxt5_bridge import dxt5_pc_fixture
from test_texture_visual_pair_gate import make_pack
from private_undercover_dxt5_stream_stage import (
    compatible_pairs, plan_undercover_dxt5, stage_undercover_dxt5_copy)
from texture_metadata_pixel_bridge import parse_pack
from pc_texture_header_overlay_gate import _source_image_span
from private_carbon_dxt1_stream_stage import section_span


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.donor = make_pack('ps2', bits=8)
        self.pc = dxt5_pc_fixture(mips=2)
        self.bun, self.stream = bundle(142, self.pc)

    def test_dimension_matches_are_stable_private_ordinals(self):
        self.assertEqual(compatible_pairs(self.donor, self.pc), [(0,0,8,8),(1,0,8,8)])

    def test_auto_plan_covers_existing_image_only(self):
        p = plan_undercover_dxt5(self.bun, len(self.stream), self.pc, self.donor)
        self.assertEqual(p['compatible_pairs'], 2)
        self.assertEqual((p['donor_ordinal'], p['pc_dxt5_slot']), (0,0))
        self.assertTrue(p['automatic_selection'])
        self.assertGreater(p['stats']['changed_image_bytes'], 0)
        self.assertEqual(len(p['original_image']), len(p['replacement_image']))
        self.assertEqual(len(p['original_image']), 80)  # 8x8, 2 DXT5 mips
        self.assertNotEqual(p['original_image'], p['replacement_image'])

    def test_explicit_ordinals_are_respected(self):
        p = plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor,
                                 142,0,0)
        self.assertFalse(p['automatic_selection'])

    def test_missing_second_ordinal_rejected(self):
        for x, y in ((0,None),(None,0)):
            with self.subTest(pair=(x,y)), self.assertRaisesRegex(ValueError,'both'):
                plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor,
                                     142,x,y)

    def test_bool_and_negative_ordinal_rejected(self):
        for x,y in ((True,0),(0,True),(-1,0),(0,-2)):
            with self.subTest(pair=(x,y)), self.assertRaisesRegex(ValueError,'ordinal'):
                plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor,
                                     142,x,y)

    def test_out_of_range_ordinals_rejected(self):
        for x,y in ((2,0),(0,42)):
            with self.subTest(pair=(x,y)), self.assertRaisesRegex(ValueError,'out of range'):
                plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor,
                                     142,x,y)

    def test_mismatched_dimensions_fail_closed(self):
        wrong=dxt5_pc_fixture(w=16,h=16)
        b,s=bundle(142,wrong)
        with self.assertRaisesRegex(ValueError,'No exact-dimension'):
            plan_undercover_dxt5(b,len(s),wrong,self.donor)

    def test_broken_selected_bundle_span_rejected(self):
        with self.assertRaisesRegex(ValueError,'table row'):
            plan_undercover_dxt5(self.bun,len(self.stream),self.pc[:-1],self.donor)

    def test_unsupported_pc_section_rejected(self):
        with self.assertRaises(ValueError):
            plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor,141)

    def test_in_memory_reversal_is_byte_exact(self):
        plan=plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor)
        a=plan['change_start']
        new=bytearray(self.stream)
        new[a:a+len(plan['replacement_image'])]=plan['replacement_image']
        self.assertEqual(new[:a],self.stream[:a])
        self.assertEqual(new[a+len(plan['replacement_image']):],
                         self.stream[a+len(plan['replacement_image']):])
        new[a:a+len(plan['original_image'])]=plan['original_image']
        self.assertEqual(bytes(new),self.stream)

    def test_matching_pair_does_not_mutate_input_sections(self):
        previous=(self.pc,self.donor)
        plan_undercover_dxt5(self.bun,len(self.stream),self.pc,self.donor)
        self.assertEqual(previous,(self.pc,self.donor))


class PrivateStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.uc,self.bun,self.stream=source_fixture(self.base,with_pc=True)
        self.orig={p:p.read_bytes() for p in (self.uc,self.bun,self.stream)}
        self.out=self.base/'STAGED_STREAML5RB_PRIVATE.BUN'

    def tearDown(self):
        self.tmp.cleanup()

    def run_stage(self,**kwargs):
        return stage_undercover_dxt5_copy(self.uc,self.bun,self.stream,**kwargs)

    def test_default_dry_run_never_writes(self):
        before=set(self.base.iterdir())
        result=self.run_stage()
        self.assertFalse(result['private_copy_created'])
        self.assertTrue(result['originals_unchanged'])
        self.assertEqual(set(self.base.iterdir()),before)
        self.assertTrue(all(p.read_bytes()==data for p,data in self.orig.items()))

    def test_report_contains_no_private_paths_texture_hashes_or_pixels(self):
        report=json.dumps(self.run_stage())
        self.assertNotIn(str(self.base),report)
        self.assertNotIn('286331153',report)
        self.assertNotIn('L5RB.BUN',report)
        self.assertNotIn('RGBA',report)

    def test_optin_write_roundtrip_and_neighbor_preservation(self):
        result=self.run_stage(write_private_copy=True,private_output=self.out)
        self.assertTrue(result['private_copy_created'])
        original=self.orig[self.stream]
        actual=self.out.read_bytes()
        self.assertEqual(len(actual),len(original))
        self.assertNotEqual(actual,original)
        pc_off,n=section_span(self.orig[self.bun],len(original),142)
        section=original[pc_off:pc_off+n]
        meta=next(m for _,m in sorted(parse_pack(section,'pc')['records'].items())
                  if m['codec']==38)
        left,right=_source_image_span(section,meta)
        self.assertEqual(actual[:pc_off+left],original[:pc_off+left])
        self.assertEqual(actual[pc_off+right:],original[pc_off+right:])
        self.assertEqual(parse_pack(actual[pc_off:pc_off+n],'pc')['records'],
                         parse_pack(section,'pc')['records'])
        reverted=bytearray(actual)
        reverted[pc_off+left:pc_off+right]=original[pc_off+left:pc_off+right]
        self.assertEqual(bytes(reverted),original)
        self.assertTrue(all(p.read_bytes()==data for p,data in self.orig.items()))

    def test_explicit_pair_accepted(self):
        report=self.run_stage(donor_ordinal=0,pc_dxt5_slot=0)
        self.assertFalse(report['automatic_dimension_match'])

    def test_write_requires_explicit_output(self):
        with self.assertRaisesRegex(ValueError,'Explicit new private output'):
            self.run_stage(write_private_copy=True)

    def test_output_requires_explicit_write(self):
        with self.assertRaisesRegex(ValueError,'requires explicit write'):
            self.run_stage(private_output=self.out)
        self.assertFalse(self.out.exists())

    def test_existing_output_is_never_overwritten(self):
        self.out.write_text('KEEP')
        with self.assertRaisesRegex(ValueError,'NEW STAGED_'):
            self.run_stage(write_private_copy=True,private_output=self.out)
        self.assertEqual(self.out.read_text(),'KEEP')

    def test_wrong_output_filename_rejected(self):
        for name in ('STREAML5RB.BUN','test.BUN'):
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'NEW STAGED_'):
                self.run_stage(write_private_copy=True,private_output=self.base/name)

    def test_missing_output_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,'NEW STAGED_'):
            self.run_stage(write_private_copy=True,
                           private_output=self.base/'missing'/'STAGED_STREAML5RB.BUN')

    def test_game_tracks_output_directory_rejected(self):
        folder=self.base/'TRACKS';folder.mkdir()
        with self.assertRaisesRegex(ValueError,'NEW STAGED_'):
            self.run_stage(write_private_copy=True,
                           private_output=folder/'STAGED_STREAML5RB.BUN')

    def test_symlinked_output_leaf_rejected(self):
        try:self.out.symlink_to(self.stream)
        except (OSError,NotImplementedError):self.skipTest('No symlink support')
        with self.assertRaisesRegex(ValueError,'Symlinked'):
            self.run_stage(write_private_copy=True,private_output=self.out)

    def test_symlinked_source_leaf_rejected(self):
        path=self.base/'alias.zip'
        try:path.symlink_to(self.uc)
        except (OSError,NotImplementedError):self.skipTest('No symlink support')
        with self.assertRaisesRegex(ValueError,'Symlinks'):
            stage_undercover_dxt5_copy(path,self.bun,self.stream)

    def test_symlinked_ancestor_rejected(self):
        folder=self.base/'alias_folder'
        try:folder.symlink_to(self.base, target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('No symlink support')
        with self.assertRaisesRegex(ValueError,'Symlinks'):
            stage_undercover_dxt5_copy(folder/self.uc.name,self.bun,self.stream)

    def test_unexpected_alias_source_files_rejected(self):
        with self.assertRaisesRegex(ValueError,'alias'):
            stage_undercover_dxt5_copy(self.stream,self.bun,self.stream)

    def test_missing_original_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing'):
            stage_undercover_dxt5_copy(self.base/'does_not_exist.zip',self.bun,self.stream)

    def test_original_source_not_modified_on_bad_destination(self):
        with self.assertRaises(ValueError):
            self.run_stage(write_private_copy=True,
                           private_output=self.base/'STREAML5RB.BUN')
        self.assertTrue(all(p.read_bytes()==data for p,data in self.orig.items()))

    def test_invalid_uc_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported Undercover'):
            self.run_stage(undercover_section=123)

    def test_invalid_pc_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported Carbon'):
            self.run_stage(carbon_section=123)

    def test_partial_ordinal_selection_rejected(self):
        with self.assertRaisesRegex(ValueError,'both'):
            self.run_stage(donor_ordinal=0)

    def test_donor_out_of_range_rejected(self):
        with self.assertRaisesRegex(ValueError,'out of range'):
            self.run_stage(donor_ordinal=300,pc_dxt5_slot=0)

    def test_wrong_dimension_pc_target_rejected(self):
        # Replace PC resource bytes with separately built wrong-dimension pack.
        bad=dxt5_pc_fixture(w=16,h=16)
        b,s=bundle(142,bad)
        self.bun.write_bytes(b);self.stream.write_bytes(s)
        with self.assertRaisesRegex(ValueError,'No exact-dimension'):
            self.run_stage()

    def test_missing_zip_member_rejected(self):
        bad=self.base/'missing_member.zip'
        with zipfile.ZipFile(bad,'w') as z:
            z.writestr('TRACKS/L2RB.BUN',b'FAKE')
        with self.assertRaises((KeyError,ValueError)):
            stage_undercover_dxt5_copy(bad,self.bun,self.stream)

    def test_wrong_boolean_write_flag_rejected(self):
        with self.assertRaisesRegex(ValueError,'write flag'):
            self.run_stage(write_private_copy=1)

    def test_cli_explicit_ordinal_flags_are_honored(self):
        import private_undercover_dxt5_stream_stage as mod
        args=['stage.py', '--undercover-ps2-zip',str(self.uc),
              '--carbon-bun',str(self.bun),'--carbon-stream',str(self.stream),
              '--undercover-section','3401','--carbon-section','142',
              '--donor-ordinal','1','--pc-dxt5-slot','0']
        out=io.StringIO()
        with patch('sys.argv',args),redirect_stdout(out):
            mod.main()
        r=json.loads(out.getvalue())
        self.assertEqual(r['donor_ordinal'],1)
        self.assertEqual(r['pc_dxt5_slot'],0)
        self.assertFalse(r['automatic_dimension_match'])
        self.assertFalse(r['private_copy_created'])

    def test_no_partial_output_on_copy_verification_failure(self):
        with patch('private_undercover_dxt5_stream_stage._verify_output',
                   side_effect=ValueError('Injected full-stream verification failure')):
            with self.assertRaisesRegex(ValueError,'Injected'):
                self.run_stage(write_private_copy=True,private_output=self.out)
        self.assertFalse(self.out.exists())

    def test_fail_if_original_stream_changes_during_staging(self):
        import private_undercover_dxt5_stream_stage as mod
        original_verify=mod._verify_output
        def changed_during_stage(*args):
            result=original_verify(*args)
            with self.stream.open('r+b') as source:
                source.seek(0)
                first=source.read(1)
                source.seek(0)
                source.write(bytes((first[0]^1,)))
            return result
        with patch.object(mod,'_verify_output',side_effect=changed_during_stage):
            with self.assertRaisesRegex(ValueError,'changed before publication'):
                self.run_stage(write_private_copy=True,private_output=self.out)
        self.assertFalse(self.out.exists())

    def test_no_output_on_bad_source_section(self):
        bad=self.base/'invalid.zip';bad.write_bytes(b'garbage')
        with self.assertRaises((ValueError,zipfile.BadZipFile)):
            stage_undercover_dxt5_copy(bad,self.bun,self.stream,
                                       write_private_copy=True,private_output=self.out)
        self.assertFalse(self.out.exists())


if __name__=='__main__':unittest.main()
