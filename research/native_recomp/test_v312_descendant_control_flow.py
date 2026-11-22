#!/usr/bin/env python3
"""V312 synthetic-only static Wii helper control-flow tests."""
import hashlib
import unittest

from audit_v312_descendant_control_flow import (
    FUNC,ORIGINAL_WORDS,analyze_words,audit
)

def sample():
    # bl +0x100; conditional no-link branch +8; blr; remaining nops.
    return [0x48000101,0x41820008,0x4e800020]+[0x60000000]*61

class Tests(unittest.TestCase):
    def test_control_flow_counts_and_exact_public_target(self):
        words=sample()
        self.assertEqual(len(words),ORIGINAL_WORDS)
        result=analyze_words(words)
        self.assertIn("words=64 calls=1 targets=1",result[0])
        self.assertIn("conditional_calls=0 conditional_branches=1",result[0])
        self.assertIn("bclr=1 bcctr=0",result[0])
        self.assertEqual(
            result[1],
            f"V312_HELPER_CALLEE rank=1 target={FUNC+0x100:08x} calls=1"
        )

    def test_all_64_original_words_required(self):
        with self.assertRaisesRegex(ValueError,"helper_geometry"):
            analyze_words(sample()[:-1])
        with self.assertRaisesRegex(ValueError,"helper_geometry"):
            analyze_words(sample(),FUNC+4)
        with self.assertRaisesRegex(ValueError,"helper_geometry"):
            analyze_words([-1]+sample()[1:])

    def test_authenticated_audit_and_wrong_sha(self):
        data=b"synthetic owner elf, no game code"
        good=audit(
            data, hashlib.sha256(data).hexdigest(),
            lambda _: {FUNC:ORIGINAL_WORDS*4},
            lambda *_: sample()
        )
        self.assertIn("original=1",good[0])
        with self.assertRaisesRegex(ValueError,"original_sha"):
            audit(data)
        with self.assertRaisesRegex(ValueError,"symbol_size"):
            audit(
                data,hashlib.sha256(data).hexdigest(),
                lambda _: {FUNC:ORIGINAL_WORDS*4-4},
                lambda *_:sample()
            )

if __name__=="__main__":
    unittest.main()
