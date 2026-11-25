import unittest
from prepare_owner_context_v720 import validate_shape
R=0x80005000
NOP=0x60000000
MTMSR=0x7c000124
RFI=0x4c000064
def mtspr(spr):return (31<<26)|((spr&31)<<16)|((spr>>5)<<11)|(467<<1)
class ContextShape(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_shape([NOP,MTMSR,mtspr(915),0x4082fffc,RFI],R),8)
        self.assertEqual(validate_shape([MTMSR,mtspr(912),mtspr(919),RFI],R),129)
    def test_refuses(self):
        for code in ([],[MTMSR],[RFI,MTMSR,RFI],[MTMSR,MTMSR,RFI],[NOP,RFI],
                     [MTMSR,0x48000005,RFI],[MTMSR,0x48000100,RFI],
                     [MTMSR,0x4e800020,RFI],[MTMSR,0x44000002,RFI],
                     [MTMSR,mtspr(913),mtspr(913),RFI]):
            with self.subTest(code=code),self.assertRaises(ValueError):validate_shape(code,R)
if __name__=='__main__':unittest.main()
