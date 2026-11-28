#!/usr/bin/env python3
"""Original-free Windows startup boundary tests; no proprietary instructions."""
import unittest

from audit_v672_si_ack_route import RESULT
from audit_v699_si_postack import STAGE, RETURN, END
from audit_v709_os_leaves import LEAVES, MAX_LOG
from test_v434_windows_startup_scope import LOGS
from windows_boot_frontier_v722 import CHECKPOINTS, classify_exit, frontier


class Tests(unittest.TestCase):
    def setUp(self):
        self.raw = LOGS['os-si-os-leaves']
        self.assertIn(RESULT, self.raw)
        self.assertIn(END, self.raw)

    def test_exact_complete_scope_still_not_game_boot(self):
        row = frontier(self.raw, 0, False, True)
        self.assertIn('last=scope_result next=none reason=scope_complete', row)
        self.assertIn('scope_verified=1 boot_verified=0', row)
        self.assertIn('exit=zero', row)

    def test_ack_and_every_ordered_native_boundary(self):
        prefix = self.raw[:self.raw.index(RESULT) + len(RESULT)]
        self.assertIn('last=ack_result next=postack reason=incomplete',
                      frontier(prefix, 0))
        for i, (name, marker) in enumerate(CHECKPOINTS):
            prefix = self.raw[:self.raw.index(marker) + len(marker)]
            wanted = CHECKPOINTS[i + 1][0] if i + 1 < len(CHECKPOINTS) else 'second_return'
            with self.subTest(stage=name):
                row = frontier(prefix, 0)
                self.assertIn(f'last={name} next={wanted} reason=incomplete', row)
                self.assertIn('scope_verified=0 boot_verified=0', row)
        prefix = self.raw[:self.raw.index(RETURN) + len(RETURN)]
        self.assertIn('last=second_return next=scope_result',
                      frontier(prefix, 0))

    def test_reject_duplicate_and_missing_ack(self):
        self.assertIn('reason=ack_missing', frontier(self.raw.replace(RESULT, b'BAD', 1), 0))
        bad = self.raw.replace(RESULT, RESULT + b'\n' + RESULT, 1)
        self.assertIn('reason=ack_duplicate', frontier(bad, 0))
        self.assertRaises(ValueError, frontier, bad, 0, False, True)

    def test_detect_order_mismatch_poll_gap_and_trailing_marker(self):
        bad = self.raw.replace(LEAVES[4], LEAVES[5], 1)
        self.assertIn('reason=unexpected', frontier(bad, 0))
        bad = self.raw.replace(b'V719_POSTACK_LOOP_POLL n=1',
                               b'V719_POSTACK_LOOP_POLL n=2', 1)
        self.assertIn('reason=poll_invalid', frontier(bad, 0))
        self.assertIn('reason=trailing', frontier(self.raw + STAGE + b'\n', 0))
        self.assertIn('reason=unexpected',
                      frontier(self.raw.replace(STAGE, LEAVES[0], 1), 0))
        self.assertRaises(ValueError, frontier, self.raw[:-len(END)-1], 0, False, True)

    def test_exit_status_and_timeout_are_distinct(self):
        for rc, timeout, kind in ((0, False, 'zero'), (124, False, 'nonzero'),
                                  (124, True, 'timeout'), (0, True, 'timeout'),
                                  (-1073741819, False, 'exception'),
                                  (0xC0000005, False, 'exception'),
                                  (1, False, 'nonzero')):
            with self.subTest(rc=rc, timeout=timeout):
                self.assertEqual(classify_exit(rc, timeout), kind)
                self.assertIn(f'exit={kind}', frontier(self.raw, rc, timeout))
                if kind != 'zero':
                    self.assertRaises(ValueError, frontier, self.raw, rc, timeout, True)

    def test_owner_log_values_never_escape(self):
        hidden = b'PRIVATE_PC=0x817abcde PRIVATE_GPR=0x12345678'
        row = frontier(self.raw + hidden + b'\n', 0, False, False)
        self.assertNotIn('PRIVATE', row)
        self.assertNotIn('0x', row)
        self.assertIn('boot_verified=0', row)
        for bad in (b'a' * (MAX_LOG + 1), 'text', 123, None):
            with self.subTest(bad_type=type(bad).__name__):
                self.assertRaises(ValueError, frontier, bad, 0)
        for args in ((True, False), (0, 1), ('0', False)):
            self.assertRaises(ValueError, classify_exit, *args)
        self.assertRaises(ValueError, frontier, self.raw, 0, False, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
