import unittest
from unittest.mock import patch
from apply_si_roots_v669 import ROOTS,TEST_SPANS,pairs,spans
from apply_irq_bootstrap_v475 import rewrite
from apply_bat_roots_v586 import PAIRS as BAT
from apply_report_table_v594 import pairs as report
class Tests(unittest.TestCase):
    def test_composition(self):
        ps=pairs();rp=report(0x805204e8)
        src='\n'.join(dict.fromkeys(a for a,b in (*BAT,*rp,*ps)))
        old=rewrite(rewrite(src,BAT),rp);out=rewrite(old,ps)
        self.assertEqual(rewrite(out,ps),out)
        self.assertIn('bat_owner(func_start)',out)
        self.assertIn('report_pc!=(func_start==0x805203c4u)',out)
        for pc in ROOTS:
            self.assertIn(f'return 0x{pc:08x}u',out)
            self.assertIn(f'func.start_address==0x{pc:08x}u',out)
        for bad in ('',old+old,old.replace('function_queue.pop();','')):
            with self.assertRaises(ValueError):rewrite(bad,ps)
    def test_ranges(self):
        with patch('apply_si_roots_v669.geometry'),patch('apply_si_roots_v669.parse_functions',return_value=dict(TEST_SPANS)),patch('apply_si_roots_v669.exact') as exact:
            self.assertEqual(spans(b'',b''),TEST_SPANS)
            self.assertEqual(exact.call_count,7)
        with self.assertRaises(ValueError):pairs(TEST_SPANS[:-1])
        with self.assertRaises(ValueError):pairs(((ROOTS[0],4096),*TEST_SPANS[1:]))
if __name__=='__main__':unittest.main()
