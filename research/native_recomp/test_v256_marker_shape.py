#!/usr/bin/env python3
"""Synthetic original-free tests of bounded V256 checkpoint diagnostics."""
import unittest
from diagnose_v256_marker_shape import classify, MARKER

RETURN = "V256_NAND_RETURN child=1 guest=1 frame=1 reply=1 mapped=1 pending=1 coherent=1 sc=1"
SHAPE = "V256_SHAPE token=16 prefix=16 fields=16 exact=16 pass=16 guest=16"

class SafeShape(unittest.TestCase):
    def test_strict_original_free_markers(self):
        guest = "\n".join(
            f"V256_NAND_GUEST callback=1 returned=1 memory=1 trial={i}"
            for i in range(1, 17)
        )
        result = classify("\n".join([MARKER, RETURN, SHAPE, guest]))
        for term in ("marker_any=1", "marker_bol=1", "marker_exact=1",
                     "marker_trim=1", "return_exact=1", "guest_exact=16",
                     "shape_exact=1"):
            self.assertIn(term, result)
        self.assertNotIn(RETURN, result)

    def test_embedded_or_indented_token_is_not_a_valid_checkpoint(self):
        sample = ("prefix "+MARKER+" suffix\n" +
                  " "+RETURN+"\n"+
                  " "+SHAPE+"\n"+
                  " V256_NAND_GUEST callback=1 returned=1 memory=1 trial=1")
        result = classify(sample)
        for term in ("marker_any=1", "marker_bol=0", "marker_exact=0",
                     "marker_trim=0", "return_any=1", "return_exact=0",
                     "guest_any=1", "guest_exact=0", "shape_exact=0"):
            self.assertIn(term, result)

    def test_whitespace_only_marker(self):
        result=classify(" "+MARKER+" \n")
        for term in ("marker_exact=0","marker_trim=1","marker_bol=0"):
            self.assertIn(term,result)

    def test_bounds_and_no_private_echo(self):
        result=classify(("prefix PRIVATE-GAME-PATH "+MARKER+"\n")*1200)
        self.assertIn("marker_any=999",result)
        self.assertNotIn("PRIVATE-GAME-PATH",result)

if __name__ == "__main__":
    unittest.main()
