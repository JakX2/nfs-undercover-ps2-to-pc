import unittest
from formatter_local_ctr_native import verify_ctr_body,ensure_ctr_resume,analyzer_local_edge,trace_ctr_destination
R=0x80010000;S=R+4;D=R+0x20
class Test(unittest.TestCase):
    def setUp(self):
        self.body=f'void fn_{R:X}(CPUContext& ctx) {{\n    switch (ctx.pc) {{\n        case 0x{D:X}: goto loc_{D:X};\n    }}\nloc_{S:X}: ;\n    // 0x{S:08X}: 4E800420\n    ++ctx.inst_count;\n    ctx.pc = ctx.ctr; return;\nloc_{D:X}: ;\n    // 0x{D:08X}: 60000000\n    ++ctx.inst_count;\n}}\n'
        self.main=f'    case 0x{R:X}: fn_{R:X}(ctx); break;\n'
    def test_analyzer(self):
        old='    block_queue.push(func_start);'
        s=analyzer_local_edge(old,R,S,D)
        self.assertIn('if(func_start==0x80010000u)',s)
        self.assertIn('local_jump_targets.insert(0x80010020u)',s)
        with self.assertRaisesRegex(ValueError,'anchor'):analyzer_local_edge(s,R,S,D)
        with self.assertRaisesRegex(ValueError,'geometry'):analyzer_local_edge(old,R,S,R+0x1000)
    def test_trace(self):
        s=self.body.replace('    ++ctx.inst_count;\n}',f'    ++ctx.inst_count;\n    formatter_nested_before(ctx,0x{D:08x}u,0x60000000u);\n}}')
        out=trace_ctr_destination(s,D,0x60000000)
        self.assertIn(f'ctx.pc == 0x{D:X}) nwii::runtime::trace_call',out)
        with self.assertRaisesRegex(ValueError,'trace'):trace_ctr_destination(out,D,0x60000000)
    def test_exact(self):self.assertTrue(verify_ctr_body(self.body,S))
    def test_resume(self):
        out,added=ensure_ctr_resume(self.main,self.body,R,S,D)
        self.assertTrue(added);self.assertIn(f'case 0x{D:X}: fn_{R:X}(ctx); break;',out)
        self.assertEqual(ensure_ctr_resume(out,self.body,R,S,D),(out,False))
    def test_body(self):
        for bad in ('ctx.pc = 0x80010020; return;','ctx.ctr--; return;','nwii::runtime::interpret_step(ctx); return;'):
            with self.assertRaisesRegex(ValueError,'CTR native body'):
                verify_ctr_body(self.body.replace('ctx.pc = ctx.ctr; return;',bad),S)
        with self.assertRaisesRegex(ValueError,'CTR native body'):verify_ctr_body(self.body+self.body,S)
    def test_conflict(self):
        with self.assertRaisesRegex(ValueError,'outer resume'):
            ensure_ctr_resume(self.main+f'    case 0x{D:X}: fn_80020000(ctx); break;\n',self.body,R,S,D)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'local resume'):
            ensure_ctr_resume(self.main,self.body.replace(f'case 0x{D:X}: goto loc_{D:X};',''),R,S,D)
        with self.assertRaisesRegex(ValueError,'destination'):
            ensure_ctr_resume(self.main,self.body.replace(f'loc_{D:X}: ;',''),R,S,D)
class ReturnBody(unittest.TestCase):
    def test_exact(self):
        from formatter_local_ctr_native import verify_blr_body
        body='loc_80010100: ;\n    // 0x80010100: 4E800020\n    ++ctx.inst_count;\n    ctx.pc = ctx.lr; return;\n'
        self.assertTrue(verify_blr_body(body,0x80010100))
        for bad in (body.replace('ctx.lr','ctx.ctr'),body.replace('4E800020','4E800420'),body.replace('++ctx.inst_count;','ctx.inst_count+=2;'),body+body):
            with self.assertRaisesRegex(ValueError,'LR native body'):verify_blr_body(bad,0x80010100)
if __name__=='__main__':unittest.main(verbosity=2)
