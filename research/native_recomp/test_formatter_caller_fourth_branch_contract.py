#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_fourth_branch_contract import extend
from audit_formatter_caller_fourth_branch import audit
from test_formatter_caller_fourth_branch import Fourth,P,N,bc,GUARD
class Contract(unittest.TestCase):
    def setUp(self):
        self.t=Fourth();self.t.setUp()
    def probe(self):
        t=self.t
        proof=audit(t.first,t.second,t.post,t.third,t.words,t.details,exact=True)
        return extend(t.third,t.words,proof)
    def test_exact(self):
        (blocks,info),reason,family=self.probe()
        self.assertEqual((reason,family,info[4:]),('admitted','integer',(True,P+68,N,P+48)))
        self.assertTrue(all(blocks[P][i]==GUARD for i in (4,7,12,15)))
    def test_shared_guard(self):
        t=self.t;w=bc(12,2,16);t.words[11]=w
        b,info=t.third;v=list(b[P]);v[11]=w;t.third=({P:tuple(v)},info[:6]+(w,info[-1]))
        self.assertEqual(self.probe(),(None,'chosen_prior_guard','integer'))
    def test_unknown(self):
        t=self.t;t.details=t.details[:4]+((False,False,None,None)+(None,)*28,)+t.details[5:]
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_existing_chosen(self):
        t=self.t;b,info=t.third;v=list(b[P])+[GUARD,N];t.third=({P:tuple(v)},info)
        self.assertEqual(self.probe(),(None,'chosen_already_admitted','integer'))
    def test_existing_alternate(self):
        t=self.t;b,info=t.third;v=list(b[P]);v[12]=N;t.third=({P:tuple(v)},info)
        self.assertEqual(self.probe(),(None,'alternate_already_admitted','integer'))
    def test_fallthrough(self):
        t=self.t;w=bc(12,0,24);t.words[11]=w
        b,info=t.third;v=list(b[P]);v[11]=w;t.third=({P:tuple(v)},info[:6]+(w,info[-1]))
        (blocks,info),reason,_=self.probe()
        self.assertEqual((reason,info[4:]),('admitted',(False,P+48,N,P+68)))
        self.assertEqual(blocks[P][17],GUARD)
if __name__=='__main__':unittest.main(verbosity=2)
