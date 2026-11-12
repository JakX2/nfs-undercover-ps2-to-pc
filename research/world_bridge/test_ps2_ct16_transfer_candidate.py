"""Independent synthetic-only checkpoints for PSMCT16 to PSMT4 address mapping."""
import hashlib
import unittest
from ps2_ct16_transfer_candidate import _addr16, decode_ct16_psmt4


class CT16CandidateTests(unittest.TestCase):
    def test_psmct16_reference_address_vectors(self):
        # Published PS2 GS column/block table coordinates; not an output-based roundtrip.
        addresses = [_addr16(x,y,64) for x,y in ((0,0),(1,0),(8,0),(0,1),(0,2),(16,0),(0,8),(32,0))]
        self.assertEqual(addresses,[0,4,2,8,64,512,256,2048])

    def test_full_page_transfer_fingerprint(self):
        # Golden result frozen after independent GS table cross-check.
        w,h=128,128
        source=bytes((i*17+i//9)%256 for i in range(w*h//2))
        indices=decode_ct16_psmt4(source,w,h)
        self.assertEqual(len(indices),w*h)
        self.assertEqual(hashlib.sha256(indices).hexdigest(),
                         'c8b5925cd7b75c6859be0de57c0499f5379800c8870ec04fba4173af2bbb42a5')

    def test_small_uninitialized_gs_transfer_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'not initialized'):
            decode_ct16_psmt4(bytes(32),8,8)

    def test_invalid_dimensions_rejected(self):
        for w,h in ((0,128),(128,0),(3,128),(128,3)):
            with self.subTest(size=(w,h)),self.assertRaisesRegex(ValueError,'dimensions|even'):
                decode_ct16_psmt4(b'',w,h)

    def test_invalid_source_length_rejected(self):
        with self.assertRaisesRegex(ValueError,'byte count'):
            decode_ct16_psmt4(bytes(10),128,128)

    def test_only_bytes_like_accepted(self):
        with self.assertRaisesRegex(ValueError,'byte count|dimensions'):
            decode_ct16_psmt4(None,128,128)


if __name__=='__main__':unittest.main()
