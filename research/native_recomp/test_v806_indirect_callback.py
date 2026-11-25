import unittest
from prepare_owner_indirect_callback_v806 import verify_indirect

class Indirect(unittest.TestCase):
    def test_exact(self):
        s='loc_80004000: ;\n    ctx.lr = 0x80004004; // save return address\n    if (ctx.ctr) { ctx.pc = ctx.ctr; return; } else nwii::runtime::note_null_call(0x80004000, ctx.lr);\nloc_80004004: ;\n'
        verify_indirect(s,0x80004000)
        for a,b in (('ctx.lr =','ctx.ctr ='),('ctx.pc = ctx.ctr','ctx.pc = ctx.lr'),('return;','micro_interpret(ctx);')):
            with self.assertRaises(ValueError):verify_indirect(s.replace(a,b),0x80004000)
        with self.assertRaises(ValueError):verify_indirect(s+s,0x80004000)
if __name__=='__main__':unittest.main()
