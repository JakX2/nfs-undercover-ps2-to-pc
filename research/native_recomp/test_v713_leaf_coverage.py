import unittest
from unittest.mock import patch
from prepare_v709_os_leaves import owns_root,entry_count,validate_coverage
class Tests(unittest.TestCase):
    def test_exact_root_and_entry(self):
        root=0x8000abcd
        for name in ('fn_8000abcd','func_8000ABCD','func_8000abcd'):
            s=f'void {name}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x8000abcd) nwii::runtime::trace_call(0x8000ABCD, ctx);\n}}\n'
            self.assertTrue(owns_root(s,root));self.assertEqual(entry_count(s,root),1)
            self.assertFalse(owns_root(s,root+4));self.assertEqual(entry_count(s,root+4),0)
            self.assertEqual(entry_count(s+s,root),2)
            self.assertEqual(entry_count(s.replace('trace_call(0x8000ABCD','trace_call(0x8000ABCE'),root),0)
    def test_strict_coverage(self):
        rows=[(0,i,0,0,0,[1,2],[]) for i in (1,2,3)]
        validate_coverage(3,{1:1,2:1,3:1},set(range(6)),rows)
        with patch('builtins.print') as out:
            for calls,entries,seen in ((0,{1:1,2:1,3:1},6),(3,{1:2,2:0,3:1},6),(3,{1:1,2:1,3:1},5)):
                with self.assertRaises(ValueError):validate_coverage(calls,entries,set(range(seen)),rows)
            self.assertEqual(out.call_count,3)
if __name__=='__main__':unittest.main()
