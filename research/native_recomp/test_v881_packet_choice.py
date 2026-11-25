import unittest
from prepare_owner_packet_choice_v881 import predicate
from validate_packet_seed_v881 import validate
H=0x80004000
class PacketChoice(unittest.TestCase):
    def test_predicate(self):
        rows={H:(0x80640000,0,0),H+4:(0x2c03ffff,0,0),H+8:(0x40820008,0,0)}
        self.assertEqual(predicate(rows),(H,H+4))
        for bad in ({**rows,H:(0x80840000,0,0)},{**rows,H+4:(0x2c030000,0,0)},{**rows,H+8:(0x48000008,0,0)}):
            with self.assertRaises(ValueError):predicate(bad)
    def test_seed(self):
        a=0x80619aa0;row=[a+32*i for i in range(4)]*2
        self.assertTrue(validate(row))
        for bad in (row[:-1],[a]*8,[a,a+32,a+64,a+100]*2,row[:4]+[a+4]+row[5:],[0x80001000+32*i for i in range(4)]*2):
            with self.assertRaises(ValueError):validate(bad)
if __name__=='__main__':unittest.main()
