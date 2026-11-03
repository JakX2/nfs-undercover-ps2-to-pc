"""Synthetic-only texture-variant ambiguity and source-provenance regressions."""
import unittest
from texture_variant_registry import TextureVariantRegistry


def metadata(w=256,h=256,codec=4,mip=1,name=b'ORIGINAL_SYNTHETIC',tile=3,offset=0):
    return {'width':w,'height':h,'codec':codec,'mip_levels':mip,'tile_mode':tile,
            'name':name,'image_offset':offset,'image_bytes':w*h*codec//8,
            'palette_offset':4096,'palette_bytes':64}


class SourceTextureVariantTests(unittest.TestCase):
    def test_different_resolutions_preserved(self):
        reg=TextureVariantRegistry({241:{11:metadata(512,512)},3401:{11:metadata(256,256,offset=500)}})
        self.assertEqual(reg.summary()['hashes_with_multiple_section_variants'],1)
        self.assertEqual(reg.summary()['multi_section_hashes_with_identical_dimensions'],0)
        self.assertEqual(reg.resolve(11,241)['width'],512)
        self.assertEqual(reg.resolve(11,3401)['width'],256)
        self.assertEqual(reg.resolve(11,3401)['image_offset'],500)

    def test_ambiguous_auto_selection_rejected(self):
        reg=TextureVariantRegistry({241:{11:metadata()},3401:{11:metadata(128,128)}})
        with self.assertRaisesRegex(ValueError,'source section required'):
            reg.resolve(11)

    def test_unambiguous_selection_allowed(self):
        reg=TextureVariantRegistry({241:{11:metadata()},3401:{22:metadata()}})
        self.assertEqual(reg.resolve(11)['width'],256)

    def test_missing_source_variant_rejected(self):
        reg=TextureVariantRegistry({241:{11:metadata()},3401:{22:metadata()}})
        with self.assertRaisesRegex(KeyError,'requested source'):
            reg.resolve(11,3401)

    def test_unknown_texture_rejected(self):
        reg=TextureVariantRegistry({241:{11:metadata()}})
        with self.assertRaises(KeyError):
            reg.resolve(99,241)

    def test_same_hash_different_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'incompatible identity'):
            TextureVariantRegistry({241:{11:metadata()},3401:{11:metadata(name=b'DIFFERENT')}})

    def test_same_hash_different_codec_rejected(self):
        with self.assertRaisesRegex(ValueError,'incompatible identity'):
            TextureVariantRegistry({241:{11:metadata()},3401:{11:metadata(codec=8)}})

    def test_same_hash_different_tile_mode_rejected(self):
        with self.assertRaisesRegex(ValueError,'incompatible identity'):
            TextureVariantRegistry({241:{11:metadata()},3401:{11:metadata(tile=5)}})

    def test_mip_count_variants_preserved(self):
        reg=TextureVariantRegistry({241:{11:metadata(mip=5)},3401:{11:metadata(mip=4)}})
        self.assertEqual(reg.summary()['multi_section_hashes_with_different_mip_counts'],1)

    def test_returns_defensive_copy(self):
        reg=TextureVariantRegistry({241:{11:metadata()}})
        result=reg.resolve(11,241)
        result['width']=42
        self.assertEqual(reg.resolve(11,241)['width'],256)

    def test_reference_coverage_and_local_provenance(self):
        reg=TextureVariantRegistry({241:{11:metadata(),22:metadata()},3401:{11:metadata()}})
        count=reg.coverage([(11,22),(11,99)],source_section=3401)
        self.assertEqual(count['reference_occurrences'],4)
        self.assertEqual(count['hashes_present_anywhere_in_examined_sections'],2)
        self.assertEqual(count['hashes_with_multiple_variants'],1)
        self.assertEqual(count['hashes_present_in_requested_section'],1)

    def test_invalid_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            TextureVariantRegistry({241:{0:metadata()}})

    def test_invalid_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            TextureVariantRegistry({241:{11:metadata(w=0)}})

    def test_empty_sections_rejected(self):
        with self.assertRaisesRegex(ValueError,'No section records'):
            TextureVariantRegistry({})

    def test_empty_coverage_rejected(self):
        reg=TextureVariantRegistry({241:{11:metadata()}})
        with self.assertRaisesRegex(ValueError,'Missing source model'):
            reg.coverage([])

if __name__=='__main__':unittest.main()
