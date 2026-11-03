"""Synthetic-only PC/PS2 texture table, material budget and donor collision tests."""
import struct
import unittest
from texture_binding_control import (parse_solid_texture_table,
    pc_material_budget,ps2_material_budget,compare_carbon,summarize_undercover)


def texture_header(hashes=(111,222), pad=4):
    b=bytearray(b'\x11'*pad+bytes(188))
    struct.pack_into('<I',b,pad+12,0x16)
    b[pad+25]=len(hashes)
    return bytes(b),b''.join(struct.pack('<II',h,0) for h in hashes)


def pc_platform(texture_indices=(0,1), polygons=(1,2), tex_count=2):
    assert len(texture_indices)==len(polygons)
    info=bytearray(b'\x11'*4+bytes(52))
    struct.pack_into('<I',info,4+8,0x12)
    struct.pack_into('<I',info,4+16,len(polygons))
    struct.pack_into('<I',info,4+44,3*sum(polygons))
    meshes=bytearray()
    for t,n in zip(texture_indices,polygons):
        r=bytearray(144)
        struct.pack_into('<I',r,0x18,t*0x01010101)
        struct.pack_into('<I',r,0x60,n)
        meshes.extend(r)
    index=bytes((2*3*sum(polygons)+3)//4*4)
    return [(0x134900,bytes(info)), (0x134b02,b'\x11'*4+bytes(meshes)),
            (0x134b03,b'\x11'*8+index),(0x134b01,b'\x11'*4+bytes(36*3))] + [(0x134c02,b'M\0\0\0')]*len(polygons)


def ps2_platform(strips=((0,1,0),(1,2,1)),group_override=None):
    """Each tuple is (texture index, polygon count, polygroup number)."""
    info=b'\x11'*4+struct.pack('<III',0x20,len(strips),16*len(strips))
    entries=b'\x11'*4
    for i,(t,n,g) in enumerate(strips):
        entries+=struct.pack('<HBBfHbbBBbb',0,n+2,n,1.,i,0,0,1,g if group_override is None else group_override,t,-1)
    return [(0x134a00,info),(0x134a01,entries),(0x134a02,b'\x11'*8+bytes(16*len(strips)))]


def profile(table=(111,222), per_texture={0:1,1:2}, platform='pc'):
    return {'texture_table':tuple(table), 'per_texture':dict(per_texture),
            'meshes':2 if platform=='pc' else None,
            'strips':2 if platform=='ps2' else None, 'polygon_groups':2,
            'triangles':sum(per_texture.values()), 'unusual_packed_texture_words':0}


class TextureBindingTests(unittest.TestCase):
    def test_texture_table_valid(self):
        hdr,buf=texture_header()
        self.assertEqual(parse_solid_texture_table(hdr,buf),(111,222))

    def test_texture_table_wrong_count_rejected(self):
        hdr,buf=texture_header()
        with self.assertRaisesRegex(ValueError,'count/table'):
            parse_solid_texture_table(hdr,buf[:-8])

    def test_invalid_table_pointer_rejected(self):
        hdr,buf=texture_header()
        b=bytearray(buf);struct.pack_into('<I',b,4,123)
        with self.assertRaisesRegex(ValueError,'pointer'):
            parse_solid_texture_table(hdr,bytes(b))

    def test_zero_table_hash_rejected(self):
        hdr,buf=texture_header()
        b=bytearray(buf);struct.pack_into('<I',b,0,0)
        with self.assertRaisesRegex(ValueError,'Zero texture'):
            parse_solid_texture_table(hdr,bytes(b))

    def test_invalid_header_version(self):
        hdr,buf=texture_header()
        b=bytearray(hdr);struct.pack_into('<I',b,4+12,999)
        with self.assertRaisesRegex(ValueError,'eSolid header'):
            parse_solid_texture_table(bytes(b),buf)

    def test_duplicate_texture_hashes_preserved(self):
        hdr,buf=texture_header((111,111))
        self.assertEqual(parse_solid_texture_table(hdr,buf),(111,111))

    def test_pc_material_budget(self):
        m=pc_material_budget(pc_platform(),2)
        self.assertEqual(m['per_texture'],{0:1,1:2})
        self.assertEqual(m['triangles'],3)

    def test_pc_out_of_range_texture(self):
        with self.assertRaisesRegex(ValueError,'out-of-range'):
            pc_material_budget(pc_platform((0,2),(1,2)),2)

    def test_pc_unusual_packed_texture_word_not_silently_assumed(self):
        data=pc_platform()
        mesh=bytearray(data[1][1]);struct.pack_into('<I',mesh,4+0x18,0x01010000)
        data[1]=(0x134b02,bytes(mesh))
        self.assertEqual(pc_material_budget(data,2)['unusual_packed_texture_words'],1)

    def test_ps2_material_budget(self):
        m=ps2_material_budget(ps2_platform(),2)
        self.assertEqual(m['per_texture'],{0:1,1:2})
        self.assertEqual(m['polygon_groups'],2)

    def test_ps2_out_of_range_texture(self):
        with self.assertRaisesRegex(ValueError,'out-of-range'):
            ps2_material_budget(ps2_platform(((0,1,0),(2,2,1))),2)

    def test_ps2_one_group_multiple_textures_rejected(self):
        with self.assertRaisesRegex(ValueError,'multiple textures'):
            ps2_material_budget(ps2_platform(((0,1,0),(1,2,0))),2)

    def test_exact_carbon_material_pair(self):
        pc={141:[(77,profile())]};ps={141:[(77,profile(platform='ps2'))]}
        r=compare_carbon(pc,ps)
        self.assertEqual(r['models_with_equal_per_texture_triangle_budgets'],1)
        self.assertEqual(r['models_with_exact_texture_hash_table'],1)

    def test_carbon_delta_kept_per_texture(self):
        pc={141:[(77,profile(per_texture={0:3,1:2}))]}
        ps={141:[(77,profile(platform='ps2'))]}
        r=compare_carbon(pc,ps)
        self.assertEqual(r['nonzero_per_texture_triangle_differences'],[2])

    def test_carbon_different_hash_table_rejected(self):
        pc={141:[(77,profile())]};ps={141:[(77,profile(table=(222,333),platform='ps2'))]}
        with self.assertRaisesRegex(ValueError,'texture tables differ'):
            compare_carbon(pc,ps)

    def test_carbon_different_texture_index_set_rejected(self):
        pc={141:[(77,profile())]};ps={141:[(77,profile(per_texture={0:3},platform='ps2'))]}
        with self.assertRaisesRegex(ValueError,'texture index sets'):
            compare_carbon(pc,ps)

    def test_carbon_missing_source_model_rejected(self):
        with self.assertRaisesRegex(ValueError,'index hash sets differ'):
            compare_carbon({141:[(1,profile())]}, {141:[(2,profile(platform='ps2'))]})

    def test_undercover_repeated_hash_different_tables_preserved(self):
        p1=profile(table=(111,222),platform='ps2')
        p2=profile(table=(333,),per_texture={0:2},platform='ps2')
        r=summarize_undercover({241:[(99,p1),(99,p2)],3401:[(99,p1)]})
        self.assertEqual(r['solid_occurrences'],3)
        self.assertEqual(r['distinct_solid_hashes'],1)
        self.assertEqual(r['model_hashes_with_more_than_one_texture_table'],1)

    def test_undercover_repeated_hash_same_table_not_false_positive(self):
        p=profile(platform='ps2')
        self.assertEqual(summarize_undercover({241:[(99,p)],3401:[(99,p)]})['model_hashes_with_more_than_one_texture_table'],0)


if __name__=='__main__':unittest.main()
