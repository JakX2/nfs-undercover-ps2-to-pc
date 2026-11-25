import unittest
from unittest.mock import patch
from prepare_v672_si_ack_route import patch_shard,patch_dispatch,patch_si,INCLUDE,POLL,OBSERVE,END,BIND,SHARD_INCLUDE,HANDLER
from prepare_v668_si_ack import INCLUDE as SI_INCLUDE,WRITE
from audit_v672_si_ack_route import inspect,EVENTS,RESULT
def source(words):
    return SHARD_INCLUDE+'\n'+f'void func_{HANDLER:X}(CPUContext& ctx) {{\n'+''.join(
        f'loc_{HANDLER+4*i:X}: ;\n    // 0x{HANDLER+4*i:08X}: {w:08X}\n    ++ctx.inst_count;\n    body();\n' for i,w in enumerate(words))+'}\n'
class Tests(unittest.TestCase):
    def test_labels(self):
        w=[0x90030000,0x60000000,0x90040000,0x4e800020];s=source(w)
        out,seen=patch_shard(s,w)
        self.assertEqual(len(seen),4);self.assertEqual(out.count('v672::before('),4)
        self.assertEqual(out.count('++ctx.inst_count;'),4)
        for bad in (out,s.replace('90040000','90050000'),s.replace('++ctx.inst_count;',''),source(w[:-1])):
            with self.assertRaises(ValueError):patch_shard(bad,w)
    def test_bindings(self):
        s='\n'.join((INCLUDE,POLL,OBSERVE,END))
        self.assertIn('v672::begin(c)',patch_dispatch(s))
        self.assertIn('v672::poll(c)',patch_dispatch(s))
        device='\n'.join((SI_INCLUDE,BIND,WRITE))
        out=patch_si(device)
        self.assertIn('arm_completion_ack',out)
        self.assertIn('si_completion_ack_trace.write',out)
        for fn,raw in ((patch_si,device),(patch_dispatch,s)):
            with self.assertRaises(ValueError):fn(raw+raw)
    def test_audit(self):
        with patch('audit_v672_si_ack_route.inspect_dispatch',return_value=('ok',True)):
            rows=EVENTS+[RESULT]
            self.assertTrue(inspect(b'\n'.join(rows),0)[1])
            for x in (rows[:-1],rows+rows,rows[::-1]):
                self.assertFalse(inspect(b'\n'.join(x),0)[1])
            self.assertFalse(inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
