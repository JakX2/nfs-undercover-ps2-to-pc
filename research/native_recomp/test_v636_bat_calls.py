import unittest
from make_v634_bat_fixture import verify_calls,MAP,END,TRAMP
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def fixture():
    words=[0x60000000]*((END-MAP)//4)
    for p,d in TRAMP:words[(p-MAP)//4]=bl(p,d)
    return words
class Tests(unittest.TestCase):
    def test_required_and_alternate(self):
        w=fixture()
        self.assertEqual(set(verify_calls(w)),set(TRAMP))
        w[0]=bl(MAP,0x80527468)
        self.assertEqual(len(verify_calls(w)),3)
        w[(TRAMP[0][0]-MAP)//4]=0x60000000
        with self.assertRaises(ValueError):verify_calls(w)
    def test_wrong_target_and_bound(self):
        w=fixture();p,d=TRAMP[1];w[(p-MAP)//4]=bl(p,d+4)
        with self.assertRaises(ValueError):verify_calls(w)
        w=fixture()
        for i in range(17):w[i]=bl(MAP+4*i,0x80527550)
        with self.assertRaises(ValueError):verify_calls(w)
if __name__=='__main__':unittest.main()
