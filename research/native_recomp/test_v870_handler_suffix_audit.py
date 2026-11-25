import unittest
from unittest.mock import patch
from audit_v870_handler_suffix import inspect
from test_v864_combined_callback import P,U,S,B,T,I,QG,EG,RG
def prefix(rows,slot):
    return tuple(l.replace(b'V807_CALLBACK_ENTRY ordinal=6',f'V807_CALLBACK_ENTRY ordinal={slot}'.encode()) for l in rows)+(S.replace(b'ordinal=6',f'ordinal={slot}'.encode()),B,T.replace(b'ordinal=6',f'ordinal={slot}'.encode()))
def markers(slot,next_slot,kind,visits=9,writes=0):
    return (f'V868_HANDLER_SUFFIX_ENTRY ordinal={slot} callback_return=1 same_tick=1'.encode(),
            f'V868_HANDLER_SUFFIX_RESULT after={slot} next={next_slot} kind={kind} visits={visits} writes={writes} executed=0 handler_return=0 boot_verified=0'.encode())
class HandlerAudit(unittest.TestCase):
    def check(self,rows,rc=0):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            return inspect(b'\n'.join(rows),rc)
    def test_valid(self):
        for rows in (P,U):
            for slot,next_slot,kind in ((6,7,1),(6,8,1),(6,12,1),(11,11,2),(11,12,1)):
                row,ok,prev=self.check((*prefix(rows,slot),*markers(slot,next_slot,kind)))
                self.assertTrue(ok);self.assertIn('handler_continuation=1',row);self.assertIn('callback_return=1',prev)
    def test_earlier_bounded_stop(self):
        for rows in ((*QG,EG,RG),(*P,S,I)):
            row,ok,_=self.check(rows)
            self.assertTrue(ok);self.assertIn('handler_continuation=0',row)
            self.assertFalse(self.check((*rows,*markers(6,7,1)))[1])
    def test_order(self):
        rows=prefix(P,6);j,s=markers(6,7,1)
        for r in (rows,(*rows,j),(*rows,s,j),(*rows,j,s,j),(*rows,j,s,s),(j,*rows,j,s),(*rows,j,s,b'V868_HANDLER_SUFFIX_INVALID reason=3 guard=4 handler=0 visits=2 writes=1')):
            self.assertFalse(self.check(r)[1])
        self.assertFalse(self.check((*rows,j,s),126)[1])
    def test_geometry(self):
        for slot,n,k,v,w in ((6,11,2,9,0),(11,7,1,9,0),(6,7,2,9,0),(6,7,1,129,0),(6,7,1,0,0),(6,7,1,2,2),(11,12,1,9,1)):
            self.assertFalse(self.check((*prefix(P,slot),*markers(slot,n,k,v,w)))[1])
        self.assertFalse(self.check((*prefix(P,6),*markers(11,12,1)))[1])
if __name__=='__main__':unittest.main()
