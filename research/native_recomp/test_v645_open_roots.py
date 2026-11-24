import unittest
from apply_open_roots_v645 import pairs,IRQ_ROOTS,irq_spans
from unittest.mock import patch
from apply_bat_roots_v586 import PAIRS
from apply_report_table_v594 import pairs as report
from apply_stm_native_open_v632 import rewrite as stm
from apply_irq_bootstrap_v475 import rewrite
class Tests(unittest.TestCase):
    def test_composed(self):
        a=PAIRS;b=report(0x805204e8);c=pairs()
        src='\n'.join(dict.fromkeys(x for x,_ in (*a,*b,*c)))
        out=rewrite(rewrite(rewrite(stm(src),a),b),c)
        self.assertIn('bat_owner(func_start)',out)
        self.assertIn('report_pc!=(func_start==0x805203c4u)',out)
        self.assertIn('open_owner(func_start)',out)
        self.assertIn('func.start_address==0x805195ecu',out)
        self.assertNotIn('open_owner(func.start_address)',out)
        self.assertEqual(rewrite(out,c),out)
        self.assertEqual(out.count('func.hle_hook_name = scanner.match(opcodes);'),1)
    def test_irq_scope(self):
        out='\n'.join(z for _,z in pairs())
        for pc in IRQ_ROOTS:
            self.assertIn(f'func.start_address==0x{pc:08x}u',out)
            self.assertIn(f'return 0x{pc:08x}u',out)
        with patch('apply_open_roots_v645.parse_functions',return_value={IRQ_ROOTS[0]:20,IRQ_ROOTS[1]:36}),patch('apply_open_roots_v645.exact_words',side_effect=lambda d,e,p,n:(0,)*(n-1)+(0x4e800020,)):
            self.assertEqual(irq_spans(b'',b''),((IRQ_ROOTS[0],20),(IRQ_ROOTS[1],36)))
        with patch('apply_open_roots_v645.parse_functions',return_value={IRQ_ROOTS[0]:24,IRQ_ROOTS[1]:36}):
            with self.assertRaises(ValueError):irq_spans(b'',b'')
    def test_refusal(self):
        src='\n'.join(a for a,_ in pairs())
        for bad in (src+src,'',src.replace('function_queue.pop();','')):
            with self.assertRaises(ValueError):rewrite(bad,pairs())
if __name__=='__main__':unittest.main()
