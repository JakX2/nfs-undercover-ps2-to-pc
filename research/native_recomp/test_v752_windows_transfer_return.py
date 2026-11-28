#!/usr/bin/env python3
"""Original-free Windows V752 fourth-call SI transfer return."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_v434_windows_startup_scope import OS_SI_HANDLER_TIME, log
from windows_transfer_prefix_v751 import plan
from windows_transfer_return_v752 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build
from audit_v777_transfer_return import HANDOFF

ENTRY = b'V768_TRANSFER_ENTRY channel=1 type=1 idle=1'
RESULT = (b'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1'
          b' idle=1 irq_lane=2 reads=2 writes=3 follow=3 pending=0 total=120'
          b' handler_instruction_executed=0 boot_verified=0')
TAIL = [ENTRY, HANDOFF, RESULT]


def sample(tail=None, prefix=None):
    return log((OS_SI_HANDLER_TIME if prefix is None else prefix) +
               (TAIL if tail is None else tail))


class WindowsTransferReturnTests(unittest.TestCase):
    def test_exact_plan_and_scope(self):
        p = plan('os-si-handler-time', False, False, False, True)
        self.assertEqual(p.env, {'UNDERCOVER_V747_TIME_SUFFIX': '1',
                                 'UNDERCOVER_V777_TRANSFER_RETURN': '1'})
        self.assertEqual(p.analyzer, ('--transfer-prefix', '--transfer-return'))
        self.assertEqual(p.observers, (
            ('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),
            ('transfer_return_observer', 'prepare_v777_transfer_return.py')))
        for args in (
            ('startup', False, False, False, True),
            ('os-si-handler-time', True, False, False, True),
            ('os-si-handler-time', False, True, False, True),
            ('os-si-handler-time', False, False, True, True),
            ('os-si-handler-time', False, False, False, 1),
        ):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    plan(*args)

    def test_cli_wiring_and_refusal(self):
        import inspect as std_inspect
        self.assertIn('owner_transfer_return', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-transfer-return', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                for extra in ([], ['--owner-transfer-prefix']):
                    p = subprocess.run([sys.executable, str(runner),
                                        str(root/'missing-upstream'), str(root/'fresh-work'),
                                        '--owner-scope', 'os-si-handler-time',
                                        '--owner-transfer-return', *extra],
                                       capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=transfer_scope', p.stdout)

    def test_idle_completed_and_pending(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('transfer_return_verified=1 idle=1 reads=2 writes=3 follow=3 pending=0', row)
        pending = RESULT.replace(b'follow=3 pending=0', b'follow=2 pending=1')
        row, ok = inspect(sample([ENTRY, HANDOFF, pending]), 0)
        self.assertTrue(ok, row)
        self.assertIn('follow=2 pending=1', row)
        self.assertIn('handler_return=0 boot_verified=0', row)
        for event in TAIL:
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' original=secret'))

    def test_busy_does_not_claim_mmio(self):
        busy = RESULT.replace(b'idle=1', b'idle=0').replace(
            b'reads=2 writes=3 follow=3 pending=0', b'reads=0 writes=0 follow=0 pending=0')
        entry = ENTRY.replace(b'idle=1', b'idle=0')
        row, ok = inspect(sample([entry, HANDOFF, busy]), 0)
        self.assertTrue(ok, row)
        self.assertIn('transfer_return_verified=1 idle=0 reads=0 writes=0 follow=0 pending=0', row)
        self.assertFalse(inspect(sample([entry, HANDOFF, RESULT]), 0)[1])

    def test_exact_tail_and_semantic_rejections(self):
        for bad in (
            TAIL[:2], TAIL[::-1], [ENTRY, RESULT, HANDOFF],
            [ENTRY, HANDOFF, RESULT, b'extra after stop'],
            [b'extra before entry', *TAIL],
            [ENTRY, b'extra before handoff', HANDOFF, RESULT],
            [ENTRY, HANDOFF, b'V777_TRANSFER_MMIO_INVALID kind=1 reason=4', RESULT],
            [ENTRY, HANDOFF, RESULT.replace(b'original_return=1', b'original_return=0')],
            [ENTRY, HANDOFF, RESULT.replace(b'handler_instruction_executed=0', b'handler_instruction_executed=1')],
            [ENTRY, HANDOFF, RESULT.replace(b'pending=0', b'pending=1')],
            [ENTRY, HANDOFF, RESULT.replace(b'follow=3', b'follow=0')],
            [ENTRY, HANDOFF, RESULT.replace(b'irq_restore=1', b'irq_restore=0')],
            [ENTRY, HANDOFF, RESULT.replace(b'total=120', b'total=999')],
            [ENTRY, HANDOFF, RESULT.replace(b'reads=2', b'reads=1')],
            [ENTRY, HANDOFF, RESULT.replace(b'writes=3', b'writes=2')],
            [ENTRY, HANDOFF, RESULT.replace(b'writes=3', b'writes=64')],
        ):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(sample(bad), 0)[1])

    def test_predecessor_and_exit_rejections(self):
        for before in (OS_SI_HANDLER_TIME[:-1],
                       [*OS_SI_HANDLER_TIME, OS_SI_HANDLER_TIME[-1]],
                       [ENTRY, *OS_SI_HANDLER_TIME],
                       [HANDOFF, *OS_SI_HANDLER_TIME],
                       [b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0',
                        *OS_SI_HANDLER_TIME]):
            self.assertFalse(inspect(sample(prefix=before), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])
        for args in ((b'x'*(8*1024*1024+1), 0, False),
                     ('text', 0, False), (sample(), True, False),
                     (sample(), 0, 1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
