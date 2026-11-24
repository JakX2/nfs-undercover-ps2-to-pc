import unittest
from prepare_v458_debug_stack import validate,synthetic_words,BLR,NOP
class Tests(unittest.TestCase):
    def test_supported(self):
        self.assertTrue(validate(synthetic_words()))
        self.assertTrue(validate((NOP,BLR)))
        self.assertTrue(validate((0x48000008,NOP,BLR)))
    def test_fail_closed(self):
        bad=(0x48000001,0x4e800421,0x4086fffc,0x40860020,0x90620008,
             0x9422ffc0,0x9461ffc0,0xd8210012,0x90610104,0x38630001,BLR)
        for w in bad:
            with self.assertRaises(ValueError):validate((w,BLR))
        for words in ((),(NOP,),(NOP,)*64+(BLR,)):
            with self.assertRaises(ValueError):validate(words)
if __name__=='__main__':unittest.main()
