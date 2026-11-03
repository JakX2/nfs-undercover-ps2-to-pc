"""Synthetic-only tests: model-info hashes -> geometry index -> solid headers."""
import struct
import unittest
from geometry_hash_control import (
    parse_geometry_root, parse_solid, locate_geometry, validate_scene_geometry,
    info_hashes, read_chunks, GEOM, GEOM_HEADER, SOLID_ROOT, SOLID_HEADER,
    SOLID_TEX, SOLID_PLATFORM, MODEL_INDEX, PLATFORM_PC, PLATFORM_PS2,
    MAX_SECTION,
)


def chunk(cid, body):
    return struct.pack('<II', cid, len(body)) + body


def solid(namehash, platform=PLATFORM_PC, padding=0, auxiliary=False):
    header = b'\x11'*padding + struct.pack('<4I',0,0,0,0x16) + struct.pack('<I',namehash)
    header += bytes(max(0, 188-len(header)))
    parts = [chunk(SOLID_HEADER,header),chunk(SOLID_TEX,bytes(8))]
    if auxiliary:
        parts.append(chunk(0x13401a, bytes(12)))
    parts.append(chunk(SOLID_PLATFORM, chunk(platform, bytes(56))))
    return chunk(SOLID_ROOT,b''.join(parts))


def geometry(hashes, platform=PLATFORM_PC, padding=0, auxiliary=False):
    index = b''.join(struct.pack('<II',h,0) for h in sorted(hashes))
    header = chunk(0x134002, bytes(144)) + chunk(MODEL_INDEX,index) + chunk(0x80134008,b'')
    children = chunk(GEOM_HEADER,header)
    children += b''.join(solid(h,platform,padding if i==0 else 0,auxiliary if i==0 else False)
                         for i,h in enumerate(sorted(hashes)))
    return chunk(GEOM, bytes(8) + children)


def scene(hashes):
    return {'children':{0x34102:b''.join(struct.pack('<6I',*([0]*6)) +
                                           struct.pack('<4I',h,h,h,0) + bytes(32)
                                           for h in hashes)}}


class ModelGeometryTests(unittest.TestCase):
    def test_pc_geometry_and_info_join(self):
        g=parse_geometry_root(geometry([3,9],PLATFORM_PC,8))
        got=validate_scene_geometry(scene([3,9]),(g,),pc=True)
        self.assertEqual(got['info_hashes_backed_by_local_solids'],2)
        self.assertEqual(got['platform_chunks'],['0x00134900'])

    def test_ps2_geometry_and_info_join(self):
        g=parse_geometry_root(geometry([3,9],PLATFORM_PS2,8))
        got=validate_scene_geometry(scene([3,9]),(g,),pc=False)
        self.assertEqual(got['info_hashes_backed_by_local_solids'],2)
        self.assertEqual(got['platform_chunks'],['0x00134a00'])

    def test_multiple_pack_union(self):
        p1=parse_geometry_root(geometry([3,9],PLATFORM_PS2))
        p2=parse_geometry_root(geometry([17],PLATFORM_PS2))
        got=validate_scene_geometry(scene([3,9,17]),(p1,p2),False)
        self.assertEqual((got['geometry_packs'],got['info_hashes_unresolved_in_this_section']),(2,0))

    def test_duplicate_across_packs_is_counted_not_rejected(self):
        p1=parse_geometry_root(geometry([3,9],PLATFORM_PS2))
        p2=parse_geometry_root(geometry([9,17],PLATFORM_PS2))
        got=validate_scene_geometry(scene([3,9,17]),(p1,p2))
        self.assertEqual(got['indexed_hashes_repeated_across_packs'],1)

    def test_unresolved_info_is_reported(self):
        p=parse_geometry_root(geometry([3],PLATFORM_PS2))
        got=validate_scene_geometry(scene([3,9]),(p,))
        self.assertEqual(got['info_hashes_unresolved_in_this_section'],1)

    def test_indexed_noninfo_solid_is_counted(self):
        p=parse_geometry_root(geometry([3,9],PLATFORM_PS2))
        got=validate_scene_geometry(scene([3]),(p,))
        self.assertEqual(got['indexed_solid_hashes_not_in_local_info'],1)

    def test_two_geometry_packs_located(self):
        stream=bytes(16)+geometry([3],PLATFORM_PS2)+bytes(8)+geometry([9],PLATFORM_PS2)
        self.assertEqual(len(locate_geometry(stream)),2)

    def test_reject_geometry_without_index(self):
        r=geometry([3]);i=r.index(struct.pack('<I',MODEL_INDEX))
        broken=bytearray(r);struct.pack_into('<I',broken,i,0x123456)
        with self.assertRaisesRegex(ValueError,'Missing model index'):
            parse_geometry_root(bytes(broken))

    def test_reject_wrong_frame(self):
        r=bytearray(geometry([3]));r[8]=0x77
        with self.assertRaisesRegex(ValueError,'framing'):
            parse_geometry_root(bytes(r))

    def test_reject_index_bad_pointer(self):
        r=bytearray(geometry([3]));i=r.index(struct.pack('<I',MODEL_INDEX));struct.pack_into('<I',r,i+12,999)
        with self.assertRaisesRegex(ValueError,'nonzero serialized pointers'):
            parse_geometry_root(bytes(r))

    def test_reject_repeated_index_hash(self):
        r=bytearray(geometry([3,9]));i=r.index(struct.pack('<I',MODEL_INDEX));struct.pack_into('<I',r,i+16,3)
        with self.assertRaisesRegex(ValueError,'Unsorted, repeated'):
            parse_geometry_root(bytes(r))

    def test_reject_unsorted_index(self):
        r=bytearray(geometry([3,9]));i=r.index(struct.pack('<I',MODEL_INDEX));struct.pack_into('<I',r,i+8,9);struct.pack_into('<I',r,i+16,3)
        with self.assertRaisesRegex(ValueError,'Unsorted, repeated'):
            parse_geometry_root(bytes(r))

    def test_reject_mismatched_solid_hash(self):
        r=bytearray(geometry([3,9]));i=r.find(struct.pack('<I',SOLID_HEADER));struct.pack_into('<I',r,i+8+16,88)
        with self.assertRaisesRegex(ValueError,'exactly enumerate'):
            parse_geometry_root(bytes(r))

    def test_reject_wrong_model_platform(self):
        p=parse_geometry_root(geometry([3],PLATFORM_PC))
        with self.assertRaisesRegex(ValueError,'platform differs'):
            validate_scene_geometry(scene([3]),(p,),pc=False)

    def test_uses_filler_padding_at_12(self):
        g=parse_geometry_root(geometry([3],PLATFORM_PC,12))
        self.assertEqual(g['alignment_counts']['12'],1)

    def test_optional_solid_position_marker(self):
        g=parse_geometry_root(geometry([3],PLATFORM_PC,auxiliary=True))
        self.assertEqual(g['solid_count'],1)

    def test_invalid_version(self):
        r=bytearray(solid(3));i=r.find(struct.pack('<I',SOLID_HEADER))
        struct.pack_into('<I',r,i+8+12,0xdeadbeef)
        with self.assertRaisesRegex(ValueError,'version'):
            parse_solid(bytes(r[8:]))

    def test_reject_no_geometry_pack(self):
        with self.assertRaisesRegex(ValueError,'No validated geometry'):
            locate_geometry(bytes(128))

    def test_large_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'32 MiB'):
            locate_geometry(bytes(MAX_SECTION+1))

    def test_invalid_scinfo_size(self):
        with self.assertRaisesRegex(ValueError,'72-byte'):
            info_hashes(bytes(71))

    def test_invalid_nested_chunk_range(self):
        with self.assertRaisesRegex(ValueError,'exceeds parent'):
            list(read_chunks(struct.pack('<II',3,100),0,8))

    def test_zero_model_info_rejected(self):
        with self.assertRaisesRegex(ValueError,'Zero scenery'):
            info_hashes(bytes(72),False)


if __name__ == '__main__':
    unittest.main()
