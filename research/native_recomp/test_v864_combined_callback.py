import unittest
from unittest.mock import patch
from audit_v864_combined_callback import inspect
from test_v848_wireless_wrapper import Q,E,R,EC,RC,QG,EG,RG
from test_v852_callback_return import S,B,T,I
from test_v862_wireless_write_audit import T as W
P=(*Q,EC,RC,W)
U=(*Q,E,R)
class CombinedAudit(unittest.TestCase):
    def check(self,rows,rc=0):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            return inspect(b'\n'.join(rows),rc)
    def test_returns(self):
        for prefix,changed in ((P,1),(U,0)):
            for ordinal in (6,11):
                p=tuple(l.replace(b'V807_CALLBACK_ENTRY ordinal=6',f'V807_CALLBACK_ENTRY ordinal={ordinal}'.encode()) for l in prefix)
                row,ok=self.check((*p,S.replace(b'ordinal=6',f'ordinal={ordinal}'.encode()),B,T.replace(b'ordinal=6',f'ordinal={ordinal}'.encode())))
                self.assertTrue(ok);self.assertIn(f'write_return={changed}',row);self.assertIn('callback_return=1 outer_dispatch=1',row)
    def test_bounded_stops(self):
        for p in (P,U):
            row,ok=self.check((*p,S,I))
            self.assertTrue(ok);self.assertIn('suffix_boundary=4',row);self.assertIn('callback_return=0',row)
        row,ok=self.check((*QG,EG,RG))
        self.assertTrue(ok);self.assertIn('wireless_ordinal=5',row);self.assertIn('callback_return=0',row)
    def test_bad_order(self):
        for rows in (P,(*P,S,B),(*P,S,T,B),(*P,S,S,B,T),(*P,S,B,T,T),(*P,S,I,T),
                     (*Q,EC,RC,S,B,T),(*Q,EC,RC,S,W,B,T),(*U,W,S,B,T),(*P,W,S,B,T),
                     (S,*P,S,B,T),(*QG,EG,RG,S,B,T),
                     (*P,S,B,T,b'V861_WIRELESS_WRITE_INVALID kind=5 device=5 reason=2 witness=0 completed=12 bytes=44')):
            with self.subTest(rows=rows):self.assertFalse(self.check(rows)[1])
        self.assertFalse(self.check((*P,S,B,T),126)[1])
    def test_bad_geometry(self):
        for w in (W.replace(b'transfers=12',b'transfers=11'),W.replace(b'bytes=44',b'bytes=40'),W.replace(b'abi=1',b'abi=0')):
            self.assertFalse(self.check((*P[:-1],w,S,B,T))[1])
        for t in (T.replace(b'ordinal=6',b'ordinal=11'),T.replace(b'outer_dispatch=1',b'outer_dispatch=0'),T.replace(b'boot_verified=0',b'boot_verified=1')):
            self.assertFalse(self.check((*P,S,B,t))[1])
        self.assertFalse(self.check((*P,S,B.replace(b'visits=37',b'visits=129'),T))[1])
if __name__=='__main__':unittest.main()
