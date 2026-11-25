import unittest
from unittest.mock import patch
from pathlib import Path
from si_helper_geometry_v680 import first_edge,alias_owner
from prepare_v680_si_helper import patch_helper,verify_direct,patch_binding,exact_function
from apply_si_roots_v669 import pairs,TEST_SPANS
from audit_v672_si_ack_route import inspect,EVENTS,RESULT
HOST=Path(__file__).resolve().parent
H=0x80004000;T=0x80005000
def b(a,t):return 0x48000001|((t-a)&0x03fffffc)
def helper(words):
    return '#include "runtime/cpu_context.h"\n'+f'void func_{T:X}(CPUContext& ctx) {{\n'+''.join(
        f'loc_{T+4*i:X}: ;\n    // 0x{T+4*i:08X}: {w:08X}\n    ++ctx.inst_count;\n    body();\n' for i,w in enumerate(words))+'}\n'
class Tests(unittest.TestCase):
    def test_first_edge(self):
        words=[0x90030000,b(H+4,T),0x60000000,0x4e800421,0x4e800020]
        self.assertEqual(first_edge(H,words,{T:8}),(H+4,T,8,words[1]))
        for bad,sizes in ((words,{}),(words,{T:3}),(words,{T:4100}),([words[0],0x4e800421,*words[1:]],{T:8})):
            with self.assertRaises(ValueError):first_edge(H,bad,sizes)
    def test_shared_alias(self):
        self.assertEqual(alias_owner(T,12,{T-16:32}),(T-16,32))
        for bad in ({},{T-16:20},{T-16:32,T-8:32}):
            with self.assertRaises(ValueError):alias_owner(T,12,bad)
        ps=pairs(TEST_SPANS,T)
        self.assertNotIn(f'return 0x{T:08x}u',ps[0][1])
        self.assertIn(f'func.start_address==0x{T:08x}u',ps[2][1])
        src=helper([0x60000000,0x4e800020])
        self.assertTrue(exact_function(src,T).startswith(f'void func_{T:X}'))
        with self.assertRaises(ValueError):exact_function(src+src,T)
    def test_helper_source(self):
        words=[0x60000000,0x4e800020];s=helper(words);out,seen=patch_helper(s,T,words)
        self.assertEqual(len(seen),2);self.assertEqual(out.count('v680::before('),2)
        for bad in (helper(words[:-1]),s.replace('60000000','60000001'),s.replace('++ctx.inst_count;',''),s+s):
            with self.assertRaises(ValueError):patch_helper(bad,T,words)
        site=H+4;body=f'loc_{site:X}: ;\n    ctx.pc = 0x{T:X}; func_{T:X}(ctx);\n    if (ctx.pc != 0x{site+4:X}) return;\n'
        verify_direct(body,site,T)
        for bad in (body.replace('func_','hle_'),body.replace('if (ctx.pc !=','if (ctx.pc =='),body+body):
            with self.assertRaises(ValueError):verify_direct(bad,site,T)
        src=(HOST/'wii_si_ack_binding_v672.h').read_text()
        self.assertIn('v680::handler_boundary',patch_binding(src))
    def test_extended_audit(self):
        hs=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        good=EVENTS[:1]+hs+EVENTS[1:]+[RESULT]
        with patch('audit_v672_si_ack_route.inspect_dispatch',return_value=('ok',True)):
            row,ok=inspect(b'\n'.join(good),0);self.assertTrue(ok);self.assertIn('stages=2 helper_stages=3',row)
            for bad in (good+[hs[0]],good[:2]+good[3:],good+[b'V680_SI_HELPER_INVALID reason=4 stage=2']):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
if __name__=='__main__':unittest.main()
