import unittest
from unittest.mock import patch
from audit_v809_callback_prefix import inspect
from test_v789_alarm_suffix import A,B,C,D,E,F,BLR

X=b'V807_CALLBACK_ENTRY ordinal=6 identity=1 follow=3'
Y=b'V807_CALLBACK_RESULT original_prologue=1 save_return=1 stack_writes=8 visits=13 follow=3 continuation_executed=0 callback_return=0 boot_verified=0'

class CallbackAudit(unittest.TestCase):
    def test_valid(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for old in (B,B.replace(b'follow=2',b'follow=3')):
                for x in (X,X.replace(b'ordinal=6',b'ordinal=11')):
                    row,ok=inspect(b'\n'.join((A,old,x,Y)),0)
                    self.assertTrue(ok);self.assertIn('original_prefix=1',row)
    def test_refusals(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for rows in ((A,B),(A,B,C,D,E,F),(A,B,BLR),(A,B,Y,X),
                (X,A,B,X,Y),(A,B,X,X,Y),(A,B,X,Y,Y),
                (A,B,X.replace(b'ordinal=6',b'ordinal=7'),Y),
                (A,B,X.replace(b'identity=1',b'identity=0'),Y),
                (A,B,X.replace(b'follow=3',b'follow=2'),Y),
                (A,B,X,Y.replace(b'visits=13',b'visits=12')),
                (A,B,X,Y.replace(b'callback_return=0',b'callback_return=1')),
                (A,B,X,Y.replace(b'stack_writes=8',b'stack_writes=7')),
                (A,B.replace(b'follow=2',b'follow=0'),X,Y),
                (A,B,X,Y,b'V807_CALLBACK_INVALID kind=4 stage=5 witness=3 device=0 visits=12')):
                self.assertFalse(inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(inspect(b'\n'.join((A,B,X,Y)),126)[1])
        with patch('audit_v809_callback_prefix.alarm',return_value=('',False)):
            self.assertFalse(inspect(b'\n'.join((A,B,X,Y)),0)[1])
if __name__=='__main__':unittest.main()
