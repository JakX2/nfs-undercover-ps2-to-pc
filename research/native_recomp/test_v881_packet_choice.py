import unittest
from prepare_owner_packet_choice_v881 import predicate,first_predicate
from validate_packet_seed_v881 import validate
H=0x80004000
class PacketChoice(unittest.TestCase):
    def test_predicate(self):
        rows={H:(0x80640000,0,0),H+4:(0x2c03ffff,0,0),H+8:(0x40820008,0,0)}
        self.assertEqual(predicate(rows),([H],1,1))
        for bad in ({**rows,H:(0x60000000,0,0)},{**rows,H+4:(0x60000000,0,0)},{**rows,H+8:(0x48000008,0,0)}):
            with self.assertRaises(ValueError):predicate(bad)
    def test_nonadjacent(self):
        rows={H:(0x80640000,0,0),H+4:(0x60000000,0,0),H+8:(0x2c030000,0,0),H+12:(0x40820008,0,0)}
        self.assertEqual(predicate(rows),([H],1,1))
    def test_first_predicate(self):
        rows={H:(0x80640000,0,0),H+4:(0x60000000,0,0),H+8:(0x2c03ffff,0,0),H+12:(0x40820008,0,0)}
        self.assertEqual(first_predicate(rows),(H,H+8))
        with self.assertRaises(ValueError):first_predicate({**rows,H+8:(0x2c04ffff,0,0)})
    def test_seed(self):
        a=0x80619aa0;row=[(a+32*i,2) for i in range(4)]*2
        self.assertTrue(validate(row))
        for bad in (row[:-1],[(a,2)]*8,[(a,2),(a+32,2),(a+64,2),(a+100,2)]*2,
                    row[:4]+[(a+4,2)]+row[5:],[(0x90001000+32*i,2) for i in range(4)]*2,
                    [(a+32*i,2 if i!=1 else 3) for i in range(4)]*2):
            with self.assertRaises(ValueError):validate(bad)
if __name__=='__main__':unittest.main()
