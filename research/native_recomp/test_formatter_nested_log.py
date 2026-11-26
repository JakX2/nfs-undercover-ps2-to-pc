#!/usr/bin/env python3
import unittest
from validate_formatter_nested_log import verify,markers

def log(second=False):
    tag,_,total=markers(second);visits,loads=(44,2) if second else (35,1)
    conditional=' conditional_load=1' if second else ''
    rows=[]
    for i in range(8):
        rows.append(f'{tag}_TRIAL n={i} native_prefix=1 frame=48 loads={loads} stores=12 nonvolatile=3{conditional} pre_load_stop=1 deferred=1 reply=0 visits={visits}')
        rows.append(f'FORMATTER_NESTED_CELL_TRIAL n={i} cold_match=1 live_match={int(i!=0)} sample_equal={int(i!=0)} guest_load=0')
    return rows+['FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match=8 live_match=7 sample_equal=7 endpoint_only=1 guest_loads=0 guest_writes=0',total]
class Test(unittest.TestCase):
    def test_exact(self):
        for mode in (False,True):self.assertEqual(verify(log(mode),second=mode),tuple(log(mode)[-2:]))
    def test_duplicate(self):
        x=log();x[2]=x[0]
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x)
        x=log();x[3]=x[1]
        with self.assertRaisesRegex(ValueError,'cell trial'):verify(x)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log()[2:])
    def test_false_total(self):
        x=log();x[-2]=x[-2].replace('live_match=7','live_match=8')
        with self.assertRaisesRegex(ValueError,'totals'):verify(x)
    def test_false_equality(self):
        x=log();x[1]=x[1].replace('sample_equal=0','sample_equal=1')
        with self.assertRaisesRegex(ValueError,'consistency'):verify(x)
    def test_native_refusal(self):
        with self.assertRaisesRegex(ValueError,'refusal'):verify(log()+['FORMATTER_NESTED_REFUSAL kind=2'])
    def test_cross_mode(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log(True))
if __name__=='__main__':unittest.main(verbosity=2)
