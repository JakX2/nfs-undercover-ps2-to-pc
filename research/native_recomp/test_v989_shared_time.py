import unittest,re
from unittest.mock import patch
import audit_v989_shared_time as a
from prepare_v975_second_time import render_shared
class SharedTime(unittest.TestCase):
    def test_render(self):
        original='#pragma once\n#define UNDERCOVER_V975_PRIVATE_TIME 1\n'
        e=[(0x80004000+4*i,0x80005000,4,0,[]) for i in range(8)]
        result=render_shared(original,e,e[-1][0])
        self.assertIn('UNDERCOVER_V989_PRIVATE_SHARED 1',result)
        self.assertIn('array<AckCallEdge,8> shared_edges',result)
        self.assertIn('completion_time_call=0x8000401cu',result)
        for bad in (e[:-1],e+[e[0]]):
            with self.assertRaises(ValueError):render_shared(original,bad,e[-1][0])
        with self.assertRaises(ValueError):render_shared(original,e,e[0][0])
    def test_detail_allowlist(self):
        row=b'V989_SHARED_DETAIL phase=3 depth=0 started=0 seen=0 post=0 held=1 entries=2 returns=2 msr=0 visits=178'
        self.assertIsNotNone(re.fullmatch(a.DETAIL,row))
        for bad in (row+b' pc=0x80004000',row.replace(b'phase=3',b'phase=4'),row.replace(b'visits=178',b'visits=12345'),row.replace(b'depth=0',b'depth=9')):
            self.assertIsNone(re.fullmatch(a.DETAIL,bad))
    def test_audit(self):
        ack=b'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=48 reads=3 writes=1 boot_verified=0'
        shared=b'V989_SHARED_TIME_RESULT original_time=1 leaves=3 unchanged_msr=2 visits=44 token_preserved=1 saved_fields=38 boot_verified=0'
        post=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=61 handler_instruction_executed=0 boot_verified=0'
        with patch('audit_v967_post_ack.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join((ack,shared,post)),0)[1])
            for rows in ((ack,post),(ack,shared,post,b'V989_SHARED_DETAIL phase=3 depth=0 started=0 seen=0 post=0 held=1 entries=2 returns=2 msr=0 visits=178'),(shared,ack,post),(ack,post,shared),(ack,shared,shared,post),(ack,shared.replace(b'visits=44',b'visits=61'),post),(ack,shared,post,b'V989_SHARED_REFUSAL guard=1 frame=1 depth=1 visits=60')):
                self.assertFalse(a.inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(a.inspect(b'\n'.join((ack,shared,post)),126)[1])
        with patch('audit_v967_post_ack.inspect',return_value=('',False)):
            self.assertFalse(a.inspect(b'\n'.join((ack,shared,post)),0)[1])
if __name__=='__main__':unittest.main()
