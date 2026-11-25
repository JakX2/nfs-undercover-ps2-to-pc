import unittest
from verify_callback_resume_v853 import verify_callback_resume

class ResumeDispatch(unittest.TestCase):
    owner, pc = 0x80001000, 0x80001004
    local = 'void fn_80001000(CPUContext& ctx) {\n switch (ctx.pc) {\n case 0x80001004: goto loc_80001004;\n }\n}\n'
    outer = 'extern "C" void run_game(CPUContext& ctx) {\n switch(ctx.pc) {\n case 0x80001004: fn_80001000(ctx); break;\n }\n}\n'
    def check(self, main, body):
        verify_callback_resume(main, body, self.owner, self.pc)
    def test_nonsplit(self):
        self.check(self.local + self.outer, self.local + self.outer)
    def test_split(self):
        self.check(self.outer, self.local)
    def test_missing_outer(self):
        with self.assertRaises(ValueError): self.check(self.local, self.local)
    def test_duplicate_outer(self):
        with self.assertRaises(ValueError): self.check(self.outer.replace(' }\n}', ' case 0x80001004: fn_80001000(ctx); break;\n }\n}'), self.local)
    def test_wrong_outer_target(self):
        with self.assertRaises(ValueError): self.check(self.outer.replace('fn_80001000', 'fn_80002000'), self.local)
    def test_missing_local(self):
        with self.assertRaises(ValueError): self.check(self.outer, '')
    def test_wrong_local_target(self):
        with self.assertRaises(ValueError): self.check(self.outer, self.local.replace('goto loc_80001004','goto loc_80001008'))
    def test_duplicate_local(self):
        with self.assertRaises(ValueError): self.check(self.outer, self.local+self.local)
    def test_no_outer_case(self):
        with self.assertRaises(ValueError): self.check(self.local+self.outer.replace('case 0x80001004','case 0x80001008'),self.local)

if __name__ == '__main__': unittest.main()
