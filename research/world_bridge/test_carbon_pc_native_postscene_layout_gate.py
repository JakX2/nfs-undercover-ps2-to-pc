"""Synthetic-only adversarial source-envelope tests; no retail game assets."""
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from carbon_pc_native_postscene_layout_gate import (
    TEXTURE, GEOMETRY, SCENE, TABLE, TAIL_HEAD, TAIL_PRE, TAIL_DATA,
    TAIL_END, SCENE_CHILDREN, _frame, _children, scene_profile,
    stream_rows, _scan_roots, native_pc_postscene_profile,
    profile_carbon_section, profile_undercover_section,
    conservative_candidate_budget, inspect_private_sources,
    MEASURED_PC_PACK_TOTAL_BYTES, MEASURED_DXT5_CANDIDATE_BYTES,
)


def chunk(tag, payload):
    return struct.pack('<II',tag,len(payload))+payload


def scene(pc=True, infos=2, inst=2):
    rows=bytearray(72*infos)
    for i in range(infos):
        struct.pack_into('<II',rows,i*72+0x18,100+i if pc else 0,100+i)
    entries=bytearray(b'\x11'*4+bytes(96*inst))
    for i in range(inst):
        struct.pack_into('<h',entries,4+i*96+0x54,i%infos)
    children=(
        (SCENE_CHILDREN[0],bytes(68)),
        (SCENE_CHILDREN[1],bytes(entries)),
        (SCENE_CHILDREN[2],bytes(rows)),
        (SCENE_CHILDREN[3],bytes(32*inst)),
        (SCENE_CHILDREN[4],bytes(40)),
        (SCENE_CHILDREN[5],bytes(128)),
    )
    return chunk(SCENE,b''.join(chunk(k,v) for k,v in children))


def native_tail(groups=1):
    header=struct.pack('<6I',0x11111111,0x11111111,groups,groups,101,groups)
    b=bytearray(bytes(8)+chunk(TAIL_HEAD,header))
    for i in range(groups):
        b+=chunk(TAIL_PRE,bytes(12 if i==0 else 8))
        b+=chunk(TAIL_DATA,bytes(120))
        b+=chunk(TAIL_END,bytes(8))
    return bytes(b)


def pc_section(groups=1, zero_gap=False):
    # Every resource root starts at a 16-byte boundary.
    return (chunk(TEXTURE,bytes(8))+chunk(GEOMETRY,bytes(20 if zero_gap else 8))+
            (chunk(0,bytes(12)) if zero_gap else b'')+
            scene()+native_tail(groups))


def uc_section():
    return (chunk(TEXTURE,bytes(8)) + chunk(GEOMETRY,bytes(8))*4 +
            scene(False)+bytes(8)+chunk(0x3bc00,bytes(16)))


def fixture_bundle(entries):
    out=bytearray()
    for ident, offset, n in entries:
        row=bytearray(92)
        struct.pack_into('<h',row,8,ident)
        struct.pack_into('<II',row,20,offset,n)
        out.extend(row)
    return chunk(TABLE,bytes(out))


def fixture_stream_and_bundle(items):
    data=bytearray(2048)
    table=[]
    for sec,payload in items:
        offset=(len(data)+2047)//2048*2048
        data.extend(bytes(offset-len(data)))
        table.append((sec,offset,len(payload)))
        data.extend(payload)
    return fixture_bundle(table),bytes(data)


class FrameTests(unittest.TestCase):
    def test_frame_valid(self):
        self.assertEqual(_frame(chunk(2,b'foo'),0,2),(2,11))

    def test_frame_wrong_tag(self):
        with self.assertRaisesRegex(ValueError,'kind'):_frame(chunk(2,b''),0,3)

    def test_frame_truncated(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):_frame(b'\0'*7,0)

    def test_frame_oversize(self):
        with self.assertRaisesRegex(ValueError,'out of bounds'):_frame(struct.pack('<II',2,50),0)

    def test_children_valid(self):
        data=chunk(1,b'x')+chunk(2,b'hi')
        self.assertEqual([x[0] for x in _children(data,0,len(data))],[1,2])

    def test_children_truncated(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):_children(b'\0'*7,0,7)

    def test_children_overflow(self):
        with self.assertRaisesRegex(ValueError,'overruns'):_children(struct.pack('<II',1,12),0,8)


class SceneTests(unittest.TestCase):
    def test_pc_scene_profile(self):
        self.assertEqual(scene_profile(scene(),'pc')['first_equal_second_detail_hash_records'],2)

    def test_ps2_scene_profile(self):
        self.assertEqual(scene_profile(scene(False),'ps2')['zero_first_detail_hash_records'],2)

    def test_source_scene_wrong_platform(self):
        with self.assertRaisesRegex(ValueError,'slot'):
            scene_profile(scene(False),'pc')

    def test_pc_scene_wrong_platform(self):
        with self.assertRaisesRegex(ValueError,'slot'):
            scene_profile(scene(),'ps2')

    def test_scene_invalid_info_index(self):
        x=bytearray(scene());a=x.find(struct.pack('<I',0x34103))
        struct.pack_into('<h',x,a+8+4+0x54,99)
        with self.assertRaisesRegex(ValueError,'nonexistent'):
            scene_profile(bytes(x),'pc')

    def test_scene_extra_trailing(self):
        with self.assertRaisesRegex(ValueError,'trailing'):
            scene_profile(scene()+b'abc','pc')

    def test_scene_bad_info_count(self):
        a=scene(); c=a.find(struct.pack('<I',0x34102))
        bad=bytearray(a);bad[c:c+4]=struct.pack('<I',0x34108)
        with self.assertRaisesRegex(ValueError,'order'):
            scene_profile(bytes(bad),'pc')

    def test_scene_wrong_auxiliary_count(self):
        a=bytearray(scene());c=a.find(struct.pack('<I',0x3410d));
        a[c:c+4]=struct.pack('<I',0x34109)
        with self.assertRaisesRegex(ValueError,'order'):
            scene_profile(bytes(a),'pc')


class PostSceneTests(unittest.TestCase):
    def test_native_one(self):
        self.assertEqual(native_pc_postscene_profile(native_tail(1))['native_postscene_bytes'],204)

    def test_native_six(self):
        r=native_pc_postscene_profile(native_tail(6))
        self.assertEqual((r['native_postscene_control_groups'],r['native_postscene_bytes']),(6,1004))

    def test_native_wrong_prefix(self):
        b=b'1'+native_tail()[1:]
        with self.assertRaisesRegex(ValueError,'prefix'):
            native_pc_postscene_profile(b)

    def test_native_bad_count(self):
        b=bytearray(native_tail(1));struct.pack_into('<I',b,16+12,2)
        with self.assertRaisesRegex(ValueError,'count'):
            native_pc_postscene_profile(bytes(b))

    def test_native_bad_control_tag(self):
        b=bytearray(native_tail(1));b[60]=0xfe
        with self.assertRaisesRegex(ValueError,'kind'):
            native_pc_postscene_profile(bytes(b))

    def test_native_bad_control_length(self):
        b=bytearray(native_tail(1));struct.pack_into('<I',b,64,121)
        with self.assertRaises(ValueError):
            native_pc_postscene_profile(bytes(b))

    def test_native_extra_trailing(self):
        with self.assertRaisesRegex(ValueError,'Unrecognized'):
            native_pc_postscene_profile(native_tail()+bytes(4))

    def test_native_truncated(self):
        with self.assertRaises(ValueError):
            native_pc_postscene_profile(native_tail()[:-1])


class LayoutTests(unittest.TestCase):
    def test_carbon_one_group(self):
        r=profile_carbon_section(pc_section(1))
        self.assertEqual((r['native_postscene_control_groups'],r['native_interroot_zero_chunk_bytes']),(1,0))

    def test_carbon_six_groups_and_gap(self):
        r=profile_carbon_section(pc_section(6,True))
        self.assertEqual((r['native_postscene_control_groups'],r['native_interroot_zero_chunk_bytes']),(6,20))

    def test_undercover_four_packs(self):
        r=profile_undercover_section(uc_section())
        self.assertEqual((r['source_geometry_pack_count'],r['source_postscene_is_native_pc_372xx']),(4,False))

    def test_undercover_requires_four_packs(self):
        with self.assertRaisesRegex(ValueError,'kind'):
            profile_undercover_section(pc_section())

    def test_pc_rejects_ps2_tail(self):
        with self.assertRaises(ValueError):
            profile_carbon_section(chunk(TEXTURE,bytes(8))+chunk(GEOMETRY,bytes(8))+scene()+bytes(8)+chunk(0x3bc00,b'x'))

    def test_reject_middle_nonzero_padding(self):
        b=bytearray(pc_section(1,True));at=16+28+8;b[at]=1
        with self.assertRaisesRegex(ValueError,'nonzero'):
            profile_carbon_section(bytes(b))

    def test_reject_misaligned_root(self):
        b=chunk(TEXTURE,bytes(9))+chunk(GEOMETRY,bytes(8))+scene()+native_tail()
        with self.assertRaisesRegex(ValueError,'aligned'):
            profile_carbon_section(b)

    def test_reject_missing_scene(self):
        b=chunk(TEXTURE,bytes(8))+chunk(GEOMETRY,bytes(8))+native_tail()
        with self.assertRaises(ValueError):
            profile_carbon_section(b)

    def test_budget_feasible(self):
        carbon=profile_carbon_section(pc_section(1))
        carbon['section_bytes']=8000000
        r=conservative_candidate_budget(carbon,2272112,1176688,28664)
        self.assertTrue(r['would_fit_section_byte_budget'])
        self.assertFalse(r['same_section_id_install_safe'])
        self.assertEqual(r['max_16byte_padding_bytes'],75)

    def test_budget_rejects_oversize(self):
        carbon=profile_carbon_section(pc_section(1))
        r=conservative_candidate_budget(carbon,30000000,10000000,28664)
        self.assertFalse(r['would_fit_section_byte_budget'])

    def test_budget_rejects_noninteger(self):
        carbon=profile_carbon_section(pc_section(1))
        with self.assertRaisesRegex(ValueError,'size evidence'):
            conservative_candidate_budget(carbon,4.0,100,120)

    def test_prior_sizes_are_consistent(self):
        self.assertEqual(sum(MEASURED_PC_PACK_TOTAL_BYTES.values()),4538404)
        self.assertEqual(MEASURED_DXT5_CANDIDATE_BYTES,1176688)


class TableTests(unittest.TestCase):
    def test_two_valid_rows(self):
        r=stream_rows(fixture_bundle([(141,2048,30),(142,4096,30)]),8192)
        self.assertEqual(r[142],(4096,30))

    def test_duplicate_rows(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            stream_rows(fixture_bundle([(141,2048,30),(141,4096,30)]),8192)

    def test_overlapping_rows(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):
            stream_rows(fixture_bundle([(141,2048,3000),(142,4096,3000)]),8192)

    def test_unaligned_rows(self):
        with self.assertRaisesRegex(ValueError,'unaligned'):
            stream_rows(fixture_bundle([(141,2000,10)]),8192)

    def test_row_outside_stream(self):
        with self.assertRaisesRegex(ValueError,'out-of-range'):
            stream_rows(fixture_bundle([(141,4096,10)]),4096)

    def test_missing_table(self):
        with self.assertRaisesRegex(ValueError,'Missing'):
            stream_rows(bytes(92),8192)

    def test_ambiguous_table(self):
        b=fixture_bundle([(141,2048,30)])
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            stream_rows(b+b,8192)


class PrivateSourceTests(unittest.TestCase):
    def _write_set(self,root):
        pc_items=[(141,pc_section(6)),(142,pc_section(1,True))]
        uc_items=[(241,uc_section()),(3401,uc_section())]
        pc_bun,pc_stream=fixture_stream_and_bundle(pc_items)
        uc_bun,uc_stream=fixture_stream_and_bundle(uc_items)
        (root/'L5RB.BUN').write_bytes(pc_bun)
        (root/'STREAML5RB.BUN').write_bytes(pc_stream)
        with zipfile.ZipFile(root/'PRIVATE_TRACKS.zip','w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('TRACKS/L2RB.BUN',uc_bun)
            z.writestr('TRACKS/STREAML2RB.BUN',uc_stream)
        return root/'L5RB.BUN',root/'STREAML5RB.BUN',root/'PRIVATE_TRACKS.zip'

    def test_end_to_end_owner_fixture_no_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=self._write_set(root)
            before=[p.read_bytes() for p in files]
            r=inspect_private_sources(*files)
            self.assertEqual(r['original_undercover_ps2']['241']['source_geometry_pack_count'],4)
            self.assertTrue(r['no_original_game_files_written'])
            self.assertEqual(before,[p.read_bytes() for p in files])

    def test_reject_symlink_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=list(self._write_set(root));sym=root/'link.bun'
            sym.symlink_to(files[0]);files[0]=sym
            with self.assertRaisesRegex(ValueError,'regular files'):
                inspect_private_sources(*files)

    def test_reject_alias_files(self):
        with tempfile.TemporaryDirectory() as temp:
            files=list(self._write_set(Path(temp)));files[1]=files[0]
            with self.assertRaisesRegex(ValueError,'alias'):
                inspect_private_sources(*files)

    def test_reject_wrong_archive_member(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=list(self._write_set(root));
            with zipfile.ZipFile(files[2],'w') as z:z.writestr('WRONG',b'data')
            with self.assertRaises(KeyError):
                inspect_private_sources(*files)

    def test_reject_bad_pc_source_scene(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=self._write_set(root)
            b=bytearray(files[1].read_bytes());p=b.find(struct.pack('<I',SCENE));
            struct.pack_into('<I',b,p+8,0xdeadbeef)
            files[1].write_bytes(b)
            # Checks either invalid scene or altered shape depending on source fixture.
            with self.assertRaises(ValueError):
                inspect_private_sources(*files)


if __name__=='__main__':unittest.main()
