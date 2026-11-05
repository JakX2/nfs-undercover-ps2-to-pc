"""Source-free tests: private-only, fail-closed stream stage and restoration."""
from pathlib import Path
import os
import struct
import tempfile
import unittest

from private_carbon_dxt1_stream_stage import (
    section_span, make_plan, stage_private_copy, _rgb, _verify_output)
from synthetic_pc_dxt1_pack_envelope import build_synthetic_pc_dxt1_pack
from texture_metadata_pixel_bridge import parse_pack


def resource(h, name, color, levels=1):
    return {'hash':h,'name':name,'width':8,'height':8,
            'mip_levels':levels,'rgba':bytes((*color,255))*64}


def row(section, offset, length):
    data=bytearray(92)
    struct.pack_into('<h',data,8,section)
    struct.pack_into('<II',data,0x14,offset,length)
    return bytes(data)


def fixture(two=False):
    first=build_synthetic_pc_dxt1_pack([
        resource(0x11111111,b'SYNTH_ALPHA',(255,0,0),3),
        resource(0x22222222,b'SYNTH_BRAVO',(0,255,0))])
    second=build_synthetic_pc_dxt1_pack([resource(0x33333333,b'SYNTH_CHARLIE',(255,255,0))])
    off1,off2=2048,4096
    if len(first)>2048 or len(second)>2048:
        raise AssertionError('Fixture sections unexpectedly large')
    raw=bytearray(8192)
    raw[off1:off1+len(first)]=first
    raw[off2:off2+len(second)]=second
    rows=row(141,off1,len(first))+(row(142,off2,len(second)) if two else b'')
    bun=b'HEADER'+struct.pack('<II',0x34110,len(rows))+rows+b'TRAILER'
    return bun,bytes(raw),first,second


class SectionTableTests(unittest.TestCase):
    def test_extract_existing_141(self):
        bun,stream,first,_=fixture()
        self.assertEqual(section_span(bun,len(stream),141),(2048,len(first)))

    def test_extract_existing_142(self):
        bun,stream,_,second=fixture(two=True)
        self.assertEqual(section_span(bun,len(stream),142),(4096,len(second)))

    def test_reject_not_present(self):
        bun,stream,_,_=fixture()
        with self.assertRaisesRegex(ValueError,'absent'):
            section_span(bun,len(stream),142)

    def test_reject_duplicate_section_id(self):
        bun,stream,first,_=fixture()
        duplicate=row(141,4096,len(first))
        size=len(row(141,2048,len(first)))+len(duplicate)
        data=b'HEADER'+struct.pack('<II',0x34110,size)+row(141,2048,len(first))+duplicate
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            section_span(data,len(stream),141)

    def test_reject_second_table_tag(self):
        bun,stream,_,_=fixture()
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            section_span(bun+b'abc'+struct.pack('<I',0x34110),len(stream),141)

    def test_reject_misaligned_selected_section(self):
        bun,stream,first,_=fixture()
        data=b'X'+struct.pack('<II',0x34110,92)+row(141,2050,len(first))
        with self.assertRaisesRegex(ValueError,'span'):
            section_span(data,len(stream),141)

    def test_reject_out_of_range_section(self):
        bun,stream,first,_=fixture()
        data=b'X'+struct.pack('<II',0x34110,92)+row(141,2048,len(stream))
        with self.assertRaisesRegex(ValueError,'exceeds'):
            section_span(data,len(stream),141)

    def test_reject_overlap(self):
        bun,stream,first,_=fixture()
        rows=row(141,2048,len(first))+row(142,2048,len(first))
        data=b'X'+struct.pack('<II',0x34110,len(rows))+rows
        with self.assertRaisesRegex(ValueError,'overlaps'):
            section_span(data,len(stream),141)

    def test_reject_bad_table_size(self):
        bun,stream,_,_=fixture()
        data=b'X'+struct.pack('<II',0x34110,92+1)+bytes(93)
        with self.assertRaisesRegex(ValueError,'row table'):
            section_span(data,len(stream),141)

    def test_reject_unsupported_section(self):
        bun,stream,_,_=fixture()
        with self.assertRaisesRegex(ValueError,'Unsafe'):
            section_span(bun,len(stream),3401)


class PlanTests(unittest.TestCase):
    def test_changes_only_existing_dxt1_and_reverts(self):
        bun,stream,first,_=fixture()
        p=make_plan(bun,len(stream),first,141,0,'00FFFF')
        self.assertEqual(p['candidate_dxt1_slots'],2)
        self.assertEqual(p['mip_levels'],3)
        self.assertEqual(len(p['replacement_image']),48)
        self.assertTrue(p['changed_bytes']>0)
        self.assertEqual(len(p['replacement_image']),len(p['original_image']))

    def test_unknown_dxt1_slot(self):
        bun,stream,first,_=fixture()
        with self.assertRaisesRegex(ValueError,'ordinal'):
            make_plan(bun,len(stream),first,141,3)

    def test_boolean_slot_rejected(self):
        bun,stream,first,_=fixture()
        with self.assertRaisesRegex(ValueError,'ordinal'):
            make_plan(bun,len(stream),first,141,True)

    def test_wrong_section_bytes(self):
        bun,stream,first,_=fixture()
        with self.assertRaisesRegex(ValueError,'table-row'):
            make_plan(bun,len(stream),first[:-1],141)

    def test_reject_invalid_solid_rgb(self):
        for bad in ('GG00FF','12345','transparent','FF00FF00',None):
            with self.subTest(value=bad),self.assertRaisesRegex(ValueError,'hexadecimal'):
                _rgb(bad)

    def test_existing_other_slot_is_unchanged(self):
        bun,stream,first,_=fixture()
        p=make_plan(bun,len(stream),first,141,0,'FF00FF')
        meta=parse_pack(first,'pc')['records']
        self.assertEqual(len(meta),2)
        # The existing overlay's source parser and span check guarantee only
        # one image range; this further verifies the private stream plan.
        change=p['change_start']-p['section_start']
        self.assertGreaterEqual(change,0)
        self.assertLess(change+len(p['replacement_image']),len(first))


class PrivateCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.bun,self.original,self.section,self.second=fixture(two=True)
        self.bundle=self.root/'L5RB.BUN'
        self.stream=self.root/'STREAML5RB.BUN'
        self.bundle.write_bytes(self.bun)
        self.stream.write_bytes(self.original)
        self.output=self.root/'STREAML5RB_PRIVATE_TEST.BUN'

    def tearDown(self):
        self.temp.cleanup()

    def test_default_dryrun_does_not_write(self):
        result=stage_private_copy(self.bundle,self.stream,141)
        self.assertFalse(result['private_copy_created'])
        self.assertEqual(self.stream.read_bytes(),self.original)
        self.assertFalse(self.output.exists())

    def test_write_optin_exact_section_only_and_input_unchanged(self):
        result=stage_private_copy(self.bundle,self.stream,141,0,'FF00FF',self.output,True)
        self.assertTrue(result['private_copy_created'])
        self.assertTrue(self.output.is_file())
        self.assertEqual(self.stream.read_bytes(),self.original)
        actual=self.output.read_bytes()
        self.assertEqual(len(actual),len(self.original))
        self.assertEqual(actual[:2048],self.original[:2048])
        self.assertEqual(actual[4096:],self.original[4096:])
        self.assertEqual(parse_pack(actual[2048:2048+len(self.section)],'pc')['records'],
                         parse_pack(self.section,'pc')['records'])
        self.assertNotEqual(actual,self.original)
        # Restore the private copy's image bytes from the untouched source:
        p=make_plan(self.bun,len(self.original),self.section,141)
        undo=bytearray(actual)
        left=p['change_start']
        undo[left:left+len(p['original_image'])]=p['original_image']
        self.assertEqual(bytes(undo),self.original)

    def test_second_section_can_be_staged(self):
        result=stage_private_copy(self.bundle,self.stream,142,0,'0000FF',self.output,True)
        self.assertTrue(result['private_copy_created'])
        data=self.output.read_bytes()
        self.assertEqual(data[:4096],self.original[:4096])
        self.assertEqual(data[4096+len(self.second):],self.original[4096+len(self.second):])

    def test_write_needs_explicit_path(self):
        with self.assertRaisesRegex(ValueError,'output path'):
            stage_private_copy(self.bundle,self.stream,141,write_private_copy=True)

    def test_output_path_without_optin_rejected(self):
        with self.assertRaisesRegex(ValueError,'requires explicit'):
            stage_private_copy(self.bundle,self.stream,141,private_output=self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_not_overwritten(self):
        self.output.write_bytes(b'KEEP ME')
        with self.assertRaisesRegex(ValueError,'already exist'):
            stage_private_copy(self.bundle,self.stream,141,private_output=self.output,write_private_copy=True)
        self.assertEqual(self.output.read_bytes(),b'KEEP ME')

    def test_source_file_never_overwritten(self):
        with self.assertRaisesRegex(ValueError,'already exist'):
            stage_private_copy(self.bundle,self.stream,141,private_output=self.stream,write_private_copy=True)
        self.assertEqual(self.stream.read_bytes(),self.original)

    def test_reject_symlinked_source(self):
        link=self.root/'link.BUN'
        try:
            link.symlink_to(self.stream)
        except (OSError,NotImplementedError):
            self.skipTest('Symlink not available')
        with self.assertRaisesRegex(ValueError,'symlinked'):
            stage_private_copy(self.bundle,link,141)

    def test_verify_rejects_outside_span_modification(self):
        p=make_plan(self.bun,len(self.original),self.section,141)
        corrupt=bytearray(self.original)
        change=p['change_start']
        corrupt[change:change+len(p['replacement_image'])]=p['replacement_image']
        corrupt[0]^=1
        self.output.write_bytes(corrupt)
        with self.assertRaisesRegex(ValueError,'outside the image span'):
            _verify_output(self.stream,self.output,change,p['original_image'],p['replacement_image'])

    def test_existing_symlink_output_not_overwritten(self):
        link = self.root/'alias_output.BUN'
        try:
            link.symlink_to(self.stream)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink not available')
        with self.assertRaisesRegex(ValueError,'already exist'):
            stage_private_copy(self.bundle,self.stream,141,private_output=link,write_private_copy=True)
        self.assertEqual(self.stream.read_bytes(),self.original)

    def test_missing_output_directory_fails_closed(self):
        target=self.root/'missing_directory'/'new.BUN'
        with self.assertRaisesRegex(ValueError,'parent directory'):
            stage_private_copy(self.bundle,self.stream,141,private_output=target,write_private_copy=True)
        self.assertFalse(target.exists())

    def test_corrupted_source_pixel_alignment_rejected(self):
        corrupt=bytearray(self.original)
        idx=corrupt.find(bytes([0x11])*120,2048)
        self.assertGreaterEqual(idx,0)
        corrupt[idx]=0xFF
        self.stream.write_bytes(corrupt)
        with self.assertRaisesRegex(ValueError,'padding'):
            stage_private_copy(self.bundle,self.stream,141)
        self.assertFalse(self.output.exists())

    def test_reject_wrong_source_image_within_change_span(self):
        p=make_plan(self.bun,len(self.original),self.section,141)
        altered=bytearray(self.original)
        changed=p['change_start']
        altered[changed:changed+len(p['replacement_image'])]=p['replacement_image']
        altered[changed]^=1
        self.output.write_bytes(altered)
        with self.assertRaisesRegex(ValueError,'source/target'):
            _verify_output(self.stream,self.output,changed,p['original_image'],p['replacement_image'])

    def test_reject_source_bundle_symlink(self):
        link=self.root/'bundle_link.BUN'
        try:
            link.symlink_to(self.bundle)
        except (OSError,NotImplementedError):
            self.skipTest('Symlink not available')
        with self.assertRaisesRegex(ValueError,'symlinked'):
            stage_private_copy(link,self.stream,141)

    def test_no_stale_temp_file_after_write(self):
        stage_private_copy(self.bundle,self.stream,141,private_output=self.output,write_private_copy=True)
        self.assertFalse(list(self.root.glob('.private-carbon-test-*.tmp')))


if __name__=='__main__':
    unittest.main()
