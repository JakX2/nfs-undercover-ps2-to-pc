import unittest
from unittest.mock import patch
from audit_v852_callback_return import inspect
from test_v848_wireless_wrapper import Q,E,R,EC,RC,QG,EG,RG

P=(*Q,E,R)
S=b'V850_CALLBACK_SUFFIX_ENTRY setter_return=1 handler_ordinal=6'
B=b'V850_CALLBACK_SUFFIX_RESULT ordinal=13 target_class=0 visits=37 writes=0 polls=4 setter_return=1 callback_return=0 boot_verified=0'
T=b'V850_CALLBACK_RETURN_RESULT handler_ordinal=6 restore=1 callback_return=1 abi=1 outer_dispatch=1 visits=12 handler_instruction_executed=0 boot_verified=0'
I=B.replace(b'ordinal=13 target_class=0',b'ordinal=4 target_class=3')

class CallbackAudit(unittest.TestCase):
    def check(self,rows,rc=0):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            return inspect(b'\n'.join(rows),rc)
    def test_returns(self):
        for ordinal in (b'6',b'11'):
            p=tuple(l.replace(b'V807_CALLBACK_ENTRY ordinal=6',b'V807_CALLBACK_ENTRY ordinal='+ordinal) for l in P)
            row,ok=self.check((*p,S.replace(b'ordinal=6',b'ordinal='+ordinal),B,T.replace(b'ordinal=6',b'ordinal='+ordinal)))
            self.assertTrue(ok);self.assertIn('callback_return=1 outer_dispatch=1',row)
    def test_bounded_stops(self):
        for p,marker in (((*Q,EC,RC),'exilock_entry=1'),((*QG,EG,RG),'wireless_ordinal=5'),((*P,S,I),'suffix_boundary=4')):
            row,ok=self.check(p)
            self.assertTrue(ok);self.assertIn(marker,row);self.assertIn('callback_return=0 outer_dispatch=0',row)
    def test_invalid_sequences(self):
        for tail in ((),(S,),(S,B),(S,T,B),(B,S,T),(S,S,B,T),(S,B,T,T),(S,I,T),(S,B,T,b'V850_CALLBACK_RETURN_INVALID kind=7 suffix_stage=2 suffix_reason=0 return_stage=4 return_reason=6 device=0')):
            with self.subTest(tail=tail):self.assertFalse(self.check((*P,*tail))[1])
        self.assertFalse(self.check((S,*P,S,B,T))[1])
        self.assertFalse(self.check((*P,S,B,T),126)[1])
        for p in ((*Q,EC,RC),(*QG,EG,RG)):
            self.assertFalse(self.check((*p,S,B,T))[1])
    def test_inconsistent_markers(self):
        for b in (B.replace(b'target_class=0',b'target_class=1'),B.replace(b'visits=37',b'visits=129'),
                  B.replace(b'polls=4',b'polls=37'),B.replace(b'writes=0',b'writes=9'),
                  B.replace(b'callback_return=0',b'callback_return=1')):
            self.assertFalse(self.check((*P,S,b,T))[1])
        for t in (T.replace(b'ordinal=6',b'ordinal=11'),T.replace(b'outer_dispatch=1',b'outer_dispatch=0'),
                  T.replace(b'visits=12',b'visits=13'),T.replace(b'abi=1',b'abi=0'),
                  T.replace(b'handler_instruction_executed=0',b'handler_instruction_executed=1'),
                  T.replace(b'boot_verified=0',b'boot_verified=1')):
            self.assertFalse(self.check((*P,S,B,t))[1])
        self.assertFalse(self.check((*P,S.replace(b'ordinal=6',b'ordinal=11'),B,T))[1])
        self.assertFalse(self.check((*P,S,I.replace(b'target_class=3',b'target_class=0')))[1])
if __name__=='__main__':unittest.main()
