import unittest
from make_v1252_sleep_fixture import extend,render,SLEEP,SELECT,SIZE,ROOT,SOURCE,BLR
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
class Sleep(unittest.TestCase):
    def test_merge(self):
        body=(0x60000000,)*(SIZE//4-1)+(BLR,)
        raw=assemble({ROOT:(BLR,),SLEEP:(body[0],),SOURCE:(0x60000000,)*7},ROOT)
        csv='Name,Location,Size\n'+f'func_{ROOT:08X},{ROOT:08x},4\nfunc_{SLEEP:08X},{SLEEP:08x},4\n'
        out,symbols=extend(raw,csv,body,0x60000000)
        self.assertEqual(words_at(out,SLEEP,SIZE//4),body)
        self.assertEqual(words_at(out,SELECT,2),(0x60000000,BLR))
        self.assertIn(f'func_{SLEEP:08X},{SLEEP:08x},{SIZE}',symbols)
        self.assertIn('std::array<Word,60>',render(body,((1,2,3,4),)*3,0x60000000))
        for bad in (body[:-1],(0,)+body[1:],body[:-1]+(0,)):
            with self.assertRaises(ValueError):extend(raw,csv,bad,0x60000000)
if __name__=='__main__':unittest.main()
