import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v789_alarm_suffix import patch_private, patch_alarm, patch_handler
from prepare_v786_alarm_return import patch_handler as alarm_handler
from prepare_v778_transfer_suffix import patch_handler as transfer_handler
from prepare_v742_handler_time import patch_handler as time_handler
from prepare_v768_transfer_prefix import patch_handler as prefix_handler
from audit_v789_alarm_suffix import inspect

HERE = Path(__file__).parent
A = b'V786_ALARM_ENTRY lane=4 timer=1'
B = b'V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane=4 timer=1 deferred=1 calls=77 visits=90 polls=1 follow=2 handler_instruction_executed=0 boot_verified=0'
C = b'V726_HANDLER_CONTROL ordinal=6 kind=2 opcode=19'
D = b'V789_ALARM_BOUNDARY ordinal=6 kind=2 target_class=2 executed=0'
E = b'V778_NEXT_BOUNDARY ordinal=6 kind=2 visits=45 polls=2 follow=3 executed=0'
F = b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=45 polls=2'
BLR = b'V778_HANDLER_BLR abi=1 visits=45 polls=2 follow=3 executed=0 boot_verified=0'


class AlarmSuffix(unittest.TestCase):
    def test_private(self):
        old = 'namespace sample {\n}\n'
        new = patch_private(old, 0x80004000, 0x60000000, (0x80005000, 0x80005004))
        self.assertIn('callback_first=0x60000000u', new)
        self.assertIn('callback_sites{0x80005000u,0x80005004u}', new)
        for bad in (new, old.rstrip(), ''):
            with self.assertRaises(ValueError):
                patch_private(bad, 0, 0, (0, 4))

    def test_alarm(self):
        old = (HERE / 'wii_alarm_return_binding_v786.h').read_text()
        s = patch_alarm(old)
        self.assertIn('if(!continue_suffix())std::_Exit(0);', s)
        self.assertIn("v[0]=='1'&&v[1]=='\\0'", s)
        self.assertIn('uint32_t(c.ctr)&~3u', s)
        self.assertIn('c.mmu.read32(target)==callback_first', s)
        self.assertNotIn('c.ctr=', s)
        with self.assertRaises(ValueError):
            patch_alarm(s)

    def test_composition(self):
        old = (HERE / 'wii_si_handler_return_binding_v726.h').read_text()
        old = alarm_handler(transfer_handler(prefix_handler(time_handler(old))))
        s = patch_handler(old)
        self.assertLess(s.index('v786::returned(c,pc,w)'), s.index('witness.alarm_returned'))
        self.assertLess(s.index('witness.alarm_returned'), s.index('const bool allow='))
        self.assertLess(s.index('v786::classify'), s.index('V778_NEXT_BOUNDARY'))
        self.assertIn('(witness.completed_calls()&16u)', s)
        with self.assertRaises(ValueError):
            patch_handler(s)

    def test_audit(self):
        def check(*rows, rc=126):
            return inspect(b'\n'.join(rows), rc)[1]
        with patch('audit_v789_alarm_suffix.alarm', return_value=('', True)):
            self.assertTrue(check(A, B, C, D, E, F))
            self.assertTrue(check(A, B, BLR, rc=0))
            for klass in (1, 3, 4):
                self.assertTrue(check(A, B, C, D.replace(b'class=2', f'class={klass}'.encode()), E, F))
            self.assertTrue(check(A, B, C.replace(b'kind=2 opcode=19', b'kind=1 opcode=18'),
                                  D.replace(b'kind=2 target_class=2', b'kind=1 target_class=0'),
                                  E.replace(b'kind=2', b'kind=1'), F))
            for rows in (
                (A, C, D, E, F),
                (A, B, C, D, D, E, F),
                (A, B, C, E, D, F),
                (A, B, C, D.replace(b'executed=0', b'executed=1'), E, F),
                (A, B, C, D.replace(b'class=2', b'class=0'), E, F),
                (A, B, C, D, E.replace(b'follow=3', b'follow=0'), F),
                (A, B, C, D, E, F.replace(b'polls=2', b'polls=3')),
                (A, B, C, D, E, F.replace(b'witness=4', b'witness=3')),
                (A, B, C.replace(b'ordinal=6', b'ordinal=7'), D.replace(b'ordinal=6', b'ordinal=7'),
                 E.replace(b'ordinal=6', b'ordinal=7'), F),
            ):
                self.assertFalse(check(*rows))
            self.assertFalse(check(A, B, C, D, E, F, rc=0))
            self.assertFalse(check(A, B, BLR))
        with patch('audit_v789_alarm_suffix.alarm', return_value=('', False)):
            self.assertFalse(check(A, B, C, D, E, F))


if __name__ == '__main__':
    unittest.main()
