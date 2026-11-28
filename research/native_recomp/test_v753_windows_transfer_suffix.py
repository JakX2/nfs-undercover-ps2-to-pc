"""Original-free Windows caller continuation regression."""
import unittest
from test_v752_windows_transfer_return import sample
from windows_transfer_prefix_v751 import plan
from windows_transfer_suffix_v753 import inspect, diagnostic

CALL=[b'V726_HANDLER_CONTROL ordinal=5 kind=1 opcode=18',
      b'V778_NEXT_BOUNDARY ordinal=5 kind=1 visits=40 polls=2 follow=3 executed=0',
      b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=40 polls=2']
BLR=b'V778_HANDLER_BLR abi=1 visits=50 polls=2 follow=3 executed=0 boot_verified=0'
def log(tail):
    return sample().rstrip(b'\r\n')+b'\n'+b'\n'.join(tail)+b'\n'

class Suffix(unittest.TestCase):
    def test_plan(self):
        p=plan('os-si-handler-time',False,False,False,False,True)
        self.assertEqual(p.analyzer,('--transfer-prefix','--transfer-return'))
        self.assertEqual(p.observers[-1],('transfer_suffix_observer','prepare_v778_transfer_suffix.py'))
        self.assertEqual(p.env['UNDERCOVER_V778_TRANSFER_SUFFIX'],'1')
        for args in (('startup',False,False,False,False,True),
                     ('os-si-handler-time',True,False,False,False,True),
                     ('os-si-handler-time',False,False,False,True,True)):
            with self.assertRaises(ValueError):plan(*args)
    def test_boundaries(self):
        row,ok=inspect(log(CALL),126)
        self.assertTrue(ok,row)
        self.assertIn('ordinal=5 kind=1 follow=3',row)
        row,ok=inspect(log([BLR]),0)
        self.assertTrue(ok,row)
        self.assertIn('blr_boundary=1',row)
        for event in CALL+[BLR]:
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event+b' private=1'))
    def test_reject(self):
        for tail in (CALL[::-1],CALL[:-1],CALL+[b'extra'],
                     [CALL[0],b'extra',*CALL[1:]],
                     [CALL[0],CALL[1].replace(b'follow=3',b'follow=0'),CALL[2]],
                     [CALL[0],CALL[1],CALL[2].replace(b'polls=2',b'polls=3')]):
            self.assertFalse(inspect(log(tail),126)[1])
        for rc,timeout in ((0,False),(126,True),(0xc0000005,False)):
            self.assertFalse(inspect(log(CALL),rc,timeout)[1])
        self.assertFalse(inspect(sample(),0)[1])

if __name__=='__main__':unittest.main()
