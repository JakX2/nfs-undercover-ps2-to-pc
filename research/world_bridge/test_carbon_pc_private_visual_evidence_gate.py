#!/usr/bin/env python3
"""Source-only synthetic PNG, ROI and joint evidence regression tests."""
import contextlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest import mock
import zlib

from carbon_pc_private_visual_evidence_gate import (
    PNG_MAGIC, ROI_FORMAT, MAX_PIXELS, MAX_ROI_BYTES, MAX_SAMPLES_PER_BOX,
    decode_rgb_png, parse_roi, compare_png_evidence, attest_session_visual, main)


def chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def synth_png(width=32, height=24, pixels=None, channels=3, filter_cycle=(0,), idat_parts=1, extra=b''):
    if pixels is None:
        pixels = bytes([20, 24, 28] + ([255] if channels == 4 else [])) * (width*height)
    assert len(pixels) == width*height*channels
    rows = bytearray()
    previous = bytes(width * channels)
    for y in range(height):
        pixels_row = pixels[y*width*channels:(y+1)*width*channels]
        filt = filter_cycle[y % len(filter_cycle)]
        rows.append(filt)
        for idx, v in enumerate(pixels_row):
            left = pixels_row[idx-channels] if idx>=channels else 0
            up = previous[idx]
            up_left = previous[idx-channels] if idx>=channels else 0
            if filt == 0:predict=0
            elif filt == 1:predict=left
            elif filt == 2:predict=up
            elif filt == 3:predict=(left+up)//2
            else:
                p = left+up-up_left
                ds = (abs(p-left), abs(p-up), abs(p-up_left))
                predict = left if ds[0] <= ds[1] and ds[0] <= ds[2] else (up if ds[1] <= ds[2] else up_left)
            rows.append((v-predict)&255)
        previous = pixels_row
    compressed = zlib.compress(rows)
    ihdr = struct.pack('>IIBBBBB', width,height,8,2 if channels==3 else 6,0,0,0)
    sizes = [(len(compressed)*i)//idat_parts for i in range(idat_parts+1)]
    return PNG_MAGIC + chunk(b'IHDR', ihdr) + extra + b''.join(
        chunk(b'IDAT', compressed[sizes[i]:sizes[i+1]]) for i in range(idat_parts)) + chunk(b'IEND', b'')


def paint(w,h,rect,color=(250,10,200),base=(20,24,28)):
    rgb = bytearray(bytes(base)*(w*h))
    x0,y0,bw,bh=rect
    for y in range(y0,y0+bh):
        for x in range(x0,x0+bw):
            rgb[(y*w+x)*3:(y*w+x)*3+3]=bytes(color)
    return bytes(rgb)


class ImageDecoderTests(unittest.TestCase):
    def test_baseline(self):
        w,h,pixels=decode_rgb_png(synth_png())
        self.assertEqual((w,h), (32,24))
        self.assertEqual(pixels, bytes([20,24,28])*(w*h))

    def test_truecolor_all_filters_each(self):
        original=bytes((i*17 + i//11)%256 for i in range(13*11*3))
        for fid in range(5):
            with self.subTest(filter=fid):
                self.assertEqual(decode_rgb_png(synth_png(13,11,original,filter_cycle=(fid,)))[2],original)

    def test_mix_all_filters(self):
        data=bytes((i*21 + 49)%256 for i in range(17*17*3))
        self.assertEqual(decode_rgb_png(synth_png(17,17,data,filter_cycle=(0,1,2,3,4)))[2],data)

    def test_rgba_display_alpha_ignored(self):
        rgba = bytes(v for i in range(10*7) for v in ((i*5)%256, (i*9)%256, (i*15)%256, i%256))
        result=decode_rgb_png(synth_png(10,7,rgba,channels=4,filter_cycle=(4,)))[2]
        self.assertEqual(result,bytes(v for i in range(10*7) for v in ((i*5)%256, (i*9)%256, (i*15)%256)))

    def test_multiple_idat(self):
        self.assertEqual(decode_rgb_png(synth_png(idat_parts=4))[2],bytes([20,24,28])*768)

    def test_ancillary_metadata_ignored(self):
        img=synth_png(extra=chunk(b'tEXt',b'fake author\x00Nothing personal'))
        self.assertEqual(decode_rgb_png(img)[:2],(32,24))

    def test_reject_wrong_magic(self):
        with self.assertRaises(ValueError):decode_rgb_png(b'Not a PNG')

    def test_reject_string_not_bytes(self):
        with self.assertRaises(ValueError):decode_rgb_png('not binary')

    def test_reject_truncated(self):
        with self.assertRaises(ValueError):decode_rgb_png(synth_png()[:-3])

    def test_reject_trailing_data(self):
        with self.assertRaises(ValueError):decode_rgb_png(synth_png()+b'garbage')

    def test_reject_bad_crc(self):
        b=bytearray(synth_png());b[18]^=1
        with self.assertRaises(ValueError):decode_rgb_png(bytes(b))

    def test_reject_bad_zlib_stream(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,0)
        data=PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',b'bad zlib data')+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(data)

    def test_reject_inflated_overrun(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,0)
        data=PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(b'X'*2048))+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(data)

    def test_reject_short_inflation(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,0)
        data=PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(b'X'*11))+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(data)

    def test_reject_trailing_zlib_bytes(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,0)
        data=PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(bytes(25*8))+b'junk')+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(data)

    def test_reject_palette(self):
        ih=struct.pack('>IIBBBBB',8,8,8,3,0,0,0)
        with self.assertRaises(ValueError):decode_rgb_png(PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'PLTE',b'\xff\xff\xff')+chunk(b'IDAT',zlib.compress(bytes(9*8)))+chunk(b'IEND',b''))

    def test_reject_16bit(self):
        ih=struct.pack('>IIBBBBB',8,8,16,2,0,0,0)
        with self.assertRaises(ValueError):decode_rgb_png(PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(bytes(49*8)))+chunk(b'IEND',b''))

    def test_reject_interlaced(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,1)
        with self.assertRaises(ValueError):decode_rgb_png(PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(bytes(25*8)))+chunk(b'IEND',b''))

    def test_reject_huge_dimensions_before_decode(self):
        ih=struct.pack('>IIBBBBB',10000,10000,8,2,0,0,0)
        with self.assertRaises(ValueError):decode_rgb_png(PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(b''))+chunk(b'IEND',b''))

    def test_reject_bad_filter(self):
        ih=struct.pack('>IIBBBBB',8,8,8,2,0,0,0)
        data=PNG_MAGIC+chunk(b'IHDR',ih)+chunk(b'IDAT',zlib.compress(bytes([5])+bytes(24)+bytes(25*7)))+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(data)

    def test_reject_unknown_critical(self):
        with self.assertRaises(ValueError):decode_rgb_png(synth_png(extra=chunk(b'ABCD',b'bad')))

    def test_reject_animated(self):
        with self.assertRaises(ValueError):decode_rgb_png(synth_png(extra=chunk(b'acTL',b'animation')))

    def test_reject_repeated_ihdr(self):
        png=synth_png();ih=png[8:33]
        with self.assertRaises(ValueError):decode_rgb_png(png[:33]+ih+png[33:])

    def test_reject_out_of_order_idat(self):
        png=synth_png()
        # Split IDAT into multiple chunks with an ancillary chunk in between.
        p=33
        length=struct.unpack_from('>I',png,p)[0];idat=png[p+8:p+8+length]
        corrupt=png[:p]+chunk(b'IDAT',idat[:5])+chunk(b'tEXt',b'a\x00b')+chunk(b'IDAT',idat[5:])+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):decode_rgb_png(corrupt)


class RoiTests(unittest.TestCase):
    def setUp(self):
        self.valid={'format':ROI_FORMAT,'target':[9,5,10,10], 'anchors':[[0,0,5,5],[27,19,5,5]]}

    def parse(self,obj=None):return parse_roi(json.dumps(self.valid if obj is None else obj),32,24)

    def test_valid(self):
        self.assertEqual(self.parse()[0],(9,5,10,10))

    def test_reject_duplicate_json_fields(self):
        with self.assertRaises(ValueError):parse_roi('{"format":"'+ROI_FORMAT+'","format":"'+ROI_FORMAT+'","target":[9,5,10,10],"anchors":[[0,0,5,5],[27,19,5,5]]}',32,24)

    def test_bad_format(self):
        self.valid['format']='other'
        with self.assertRaises(ValueError):self.parse()

    def test_bad_type(self):
        self.valid['target']=[True,5,10,10]
        with self.assertRaises(ValueError):self.parse()

    def test_float_bad(self):
        self.valid['target']=[9.1,5,10,10]
        with self.assertRaises(ValueError):self.parse()

    def test_negative_bad(self):
        self.valid['target']=[-1,5,10,10]
        with self.assertRaises(ValueError):self.parse()

    def test_overflow_bad(self):
        self.valid['target']=[31,5,10,10]
        with self.assertRaises(ValueError):self.parse()

    def test_area_bad(self):
        self.valid['target']=[9,5,1,1]
        with self.assertRaises(ValueError):self.parse()

    def test_intersect_target_anchor_bad(self):
        self.valid['anchors'][0]=[8,4,5,5]
        with self.assertRaises(ValueError):self.parse()

    def test_intersect_anchor_anchor_bad(self):
        self.valid['anchors'][1]=[1,1,5,5]
        with self.assertRaises(ValueError):self.parse()

    def test_touching_edges_allowed(self):
        self.valid['anchors'][0]=[4,5,5,5]
        self.assertEqual(len(self.parse()[1]),2)

    def test_one_anchor_bad(self):
        self.valid['anchors']=[self.valid['anchors'][0]]
        with self.assertRaises(ValueError):self.parse()

    def test_nine_anchors_bad(self):
        self.valid['anchors']=self.valid['anchors']*5
        with self.assertRaises(ValueError):self.parse()

    def test_extra_roi_field_bad(self):
        self.valid['private']='x'
        with self.assertRaises(ValueError):self.parse()

    def test_non_json_bad(self):
        with self.assertRaises(ValueError):parse_roi('{this is bad}',32,24)

    def test_oversize_bad(self):
        with self.assertRaises(ValueError):parse_roi('x'*(MAX_ROI_BYTES+1),32,24)


class VisualEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.before=self.dir/'before.png';self.after=self.dir/'after.png';self.roi=self.dir/'PRIVATE_roi.json'
        self.width=32;self.height=24
        self.target=(9,5,10,10)
        self.roi.write_text(json.dumps({'format':ROI_FORMAT,'target':list(self.target),'anchors':[[0,0,5,5],[27,19,5,5]]}),encoding='utf-8')
        self.base=bytes([20,24,28])*(self.width*self.height)
        self.before.write_bytes(synth_png(self.width,self.height,self.base))
        self.after.write_bytes(synth_png(self.width,self.height,self.base))

    def put_after(self,rgb):self.after.write_bytes(synth_png(self.width,self.height,rgb,filter_cycle=(0,1,2,3,4)))

    def test_no_change(self):
        score=compare_png_evidence(self.before,self.after,self.roi)
        self.assertEqual(score['verdict'],'no_material_screen_difference_detected')
        self.assertEqual(score['target_pixels_changed_fraction'],0)

    def test_clear_localized_difference(self):
        self.put_after(paint(self.width,self.height,self.target))
        score=compare_png_evidence(self.before,self.after,self.roi)
        self.assertEqual(score['verdict'],'localized_screen_difference_candidate_not_rendering_proof')
        self.assertTrue(score['background_anchor_stability_passed'])
        self.assertEqual(score['target_pixels_changed_fraction'],1)
        self.assertEqual(score['target_sample_count'],100)
        self.assertEqual(score['background_mean_rgb_delta_0_255'],0)
        self.assertNotIn('target',score.keys())
        self.assertNotIn(str(self.dir),json.dumps(score))

    def test_background_shift_refuses(self):
        shifted=bytes([150,150,150])*(self.width*self.height)
        self.put_after(shifted)
        score=compare_png_evidence(self.before,self.after,self.roi)
        self.assertEqual(score['verdict'],'background_changed_framing_or_scene_not_controlled')

    def test_change_in_background_only(self):
        self.put_after(paint(self.width,self.height,(0,0,5,5)))
        score=compare_png_evidence(self.before,self.after,self.roi)
        self.assertFalse(score['background_anchor_stability_passed'])

    def test_small_target_delta_is_ambiguous(self):
        self.put_after(paint(self.width,self.height,self.target,color=(40,40,40)))
        score=compare_png_evidence(self.before,self.after,self.roi)
        self.assertEqual(score['verdict'],'ambiguous_screen_change_not_rendering_proof')

    def test_unchanged_anchors_but_small_target_changed_fraction(self):
        self.put_after(paint(self.width,self.height,(9,5,4,4)))
        self.assertEqual(compare_png_evidence(self.before,self.after,self.roi)['verdict'],
                         'localized_screen_difference_candidate_not_rendering_proof')

    def test_tiny_target_fraction_below_detection(self):
        self.put_after(paint(self.width,self.height,(9,5,2,2)))
        self.assertEqual(compare_png_evidence(self.before,self.after,self.roi)['verdict'],
                         'no_material_screen_difference_detected')

    def test_dimensions_mismatch(self):
        self.after.write_bytes(synth_png(20,20))
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.after,self.roi)

    def test_reject_same_path(self):
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.before,self.roi)

    def test_reject_hardlinked_input(self):
        clone=self.dir/'hardlink.png'
        try:os.link(self.before,clone)
        except (OSError,NotImplementedError):self.skipTest('Hardlinks unsupported')
        with self.assertRaises(ValueError):compare_png_evidence(self.before,clone,self.roi)

    def test_roi_symlink_rejected(self):
        alias=self.dir/'PRIVATE_roi_link.json'
        try:alias.symlink_to(self.roi)
        except (OSError,NotImplementedError):self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.after,alias)

    def test_rgb_png_rejects_invalid_roi_utf8(self):
        self.roi.write_bytes(b'\xff\xff')
        with self.assertRaises(UnicodeError):compare_png_evidence(self.before,self.after,self.roi)

    def test_reject_symlinked_input(self):
        link=self.dir/'linked.png'
        try:link.symlink_to(self.before)
        except (OSError,NotImplementedError):self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):compare_png_evidence(link,self.after,self.roi)

    def test_source_images_unchanged(self):
        before=[p.read_bytes() for p in (self.before,self.after,self.roi)]
        compare_png_evidence(self.before,self.after,self.roi)
        self.assertEqual(before,[p.read_bytes() for p in (self.before,self.after,self.roi)])
        self.assertEqual(len(list(self.dir.iterdir())),3)

    def test_invalid_roi_rejected(self):
        self.roi.write_text('{bad}',encoding='utf-8')
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.after,self.roi)

    def test_cli_compare_does_not_expose_paths(self):
        self.put_after(paint(self.width,self.height,self.target))
        with mock.patch.object(sys,'argv',['visual_gate','compare','--before-png',str(self.before),
                 '--after-png',str(self.after),'--roi-json',str(self.roi)]):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):main()
        report=json.loads(output.getvalue())
        self.assertEqual(report['verdict'],'localized_screen_difference_candidate_not_rendering_proof')
        self.assertNotIn(str(self.dir),output.getvalue())

    def test_three_shot_exact_visual_reversion(self):
        self.put_after(paint(self.width,self.height,self.target))
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(self.width,self.height,self.base))
        r=compare_png_evidence(self.before,self.after,self.roi,restored)
        self.assertEqual(r['verdict'], 'reversible_localized_screen_difference_candidate_not_rendering_proof')
        self.assertTrue(r['restoration_visual_match_to_baseline'])
        self.assertEqual(r['restored_target_rgb_delta_0_255'],0)
        self.assertEqual(len(list(self.dir.iterdir())),4)

    def test_three_shot_wrong_restored_target(self):
        self.put_after(paint(self.width,self.height,self.target))
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(self.width,self.height,paint(self.width,self.height,self.target)))
        r=compare_png_evidence(self.before,self.after,self.roi,restored)
        self.assertEqual(r['verdict'],'restored_target_differs_from_baseline_no_reversion_proof')
        self.assertFalse(r['restoration_visual_match_to_baseline'])

    def test_three_shot_restoration_camera_changes(self):
        self.put_after(paint(self.width,self.height,self.target))
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(self.width,self.height,bytes([100,100,100])*(self.width*self.height)))
        r=compare_png_evidence(self.before,self.after,self.roi,restored)
        self.assertEqual(r['verdict'],'restoration_frame_unstable_no_reversible_visual_inference')

    def test_three_shot_no_target_difference(self):
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(self.width,self.height,self.base))
        r=compare_png_evidence(self.before,self.after,self.roi,restored)
        self.assertEqual(r['verdict'],'no_material_screen_difference_detected')
        self.assertTrue(r['restoration_control_performed'])

    def test_three_shot_different_dimensions_rejected(self):
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(40,24))
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.after,self.roi,restored)

    def test_three_shot_same_source_rejected(self):
        with self.assertRaises(ValueError):compare_png_evidence(self.before,self.after,self.roi,self.before)

    def test_three_shot_cli_support(self):
        self.put_after(paint(self.width,self.height,self.target))
        restored=self.dir/'restored.png'
        restored.write_bytes(synth_png(self.width,self.height,self.base))
        with mock.patch.object(sys,'argv',['visual_gate','compare','--before-png',str(self.before),
                 '--after-png',str(self.after),'--roi-json',str(self.roi), '--restored-png',str(restored)]):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):main()
        report=json.loads(output.getvalue())
        self.assertEqual(report['verdict'],'reversible_localized_screen_difference_candidate_not_rendering_proof')
        self.assertNotIn(str(self.dir),output.getvalue())

    def test_joint_both_sources_only_candidate(self):
        self.put_after(paint(self.width,self.height,self.target))
        mock_gate=types.ModuleType('carbon_pc_private_smoke_session')
        mock_gate.evidence=lambda *args:{'scope':'SYNTHETIC_NOT_RUNTIME',
            'procmon':{'evidence_level':'some_image_bytes_read_observed_not_rendering'}}
        with mock.patch.dict(sys.modules,{'carbon_pc_private_smoke_session':mock_gate}):
            r=attest_session_visual('session','csv',self.before,self.after,self.roi)
        self.assertEqual(r['joint_verdict'],'read_span_and_localized_visual_difference_candidate_not_rendering_proof')
        self.assertTrue(r['timestamp_and_runtime_rendering_unverified'])

    def test_joint_visual_only_never_success(self):
        self.put_after(paint(self.width,self.height,self.target))
        mock_gate=types.ModuleType('carbon_pc_private_smoke_session')
        mock_gate.evidence=lambda *args:{'procmon':{'evidence_level':'exact_stream_open_only'}}
        with mock.patch.dict(sys.modules,{'carbon_pc_private_smoke_session':mock_gate}):
            r=attest_session_visual('session','csv',self.before,self.after,self.roi)
        self.assertEqual(r['joint_verdict'],'localized_visual_change_without_verified_image_read')

    def test_joint_read_only_never_success(self):
        mock_gate=types.ModuleType('carbon_pc_private_smoke_session')
        mock_gate.evidence=lambda *args:{'procmon':{'evidence_level':'full_image_span_read_observed_not_rendering'}}
        with mock.patch.dict(sys.modules,{'carbon_pc_private_smoke_session':mock_gate}):
            r=attest_session_visual('session','csv',self.before,self.after,self.roi)
        self.assertEqual(r['joint_verdict'],'image_span_read_without_controlled_visual_difference')

    def test_joint_neither(self):
        mock_gate=types.ModuleType('carbon_pc_private_smoke_session')
        mock_gate.evidence=lambda *args:{'procmon':{'evidence_level':'no_positive_exact_stream_open'}}
        with mock.patch.dict(sys.modules,{'carbon_pc_private_smoke_session':mock_gate}):
            r=attest_session_visual('session','csv',self.before,self.after,self.roi)
        self.assertEqual(r['joint_verdict'],'no_joint_image_read_and_visual_evidence')

    def test_join_propagates_real_session_failure(self):
        self.put_after(paint(self.width,self.height,self.target))
        mock_gate=types.ModuleType('carbon_pc_private_smoke_session')
        def fail(*args):raise ValueError('Installed stream is unexpected')
        mock_gate.evidence=fail
        with mock.patch.dict(sys.modules,{'carbon_pc_private_smoke_session':mock_gate}):
            with self.assertRaisesRegex(ValueError,'Installed stream'):
                attest_session_visual('session','csv',self.before,self.after,self.roi)


if __name__ == '__main__':unittest.main()
