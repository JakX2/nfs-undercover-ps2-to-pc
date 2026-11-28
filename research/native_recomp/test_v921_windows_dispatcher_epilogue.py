#!/usr/bin/env python3
"""Original-free Windows full-image RFI dependency and opt-in audit."""
import unittest
from unittest.mock import patch

from prepare_owner_context_v720 import L, RFI
from prepare_owner_scheduler_v722 import E, S
from prepare_v667_si_dispatch import DISPATCH
from prepare_v921_windows_dispatcher_epilogue import native_expectations, audit, refusal_reason
from windows_transfer_prefix_v751 import plan


class WindowsDispatcherEpilogue(unittest.TestCase):
    def test_only_deep_handler_route_admits_original_rfi_loader(self):
        combined = plan('os-si-handler-time', False, False, False,
                        combined_callback=True)
        returned = plan('os-si-handler-time', False, False, False,
                        handler_return=True)
        self.assertNotIn('--epilogue', combined.analyzer)
        self.assertEqual(returned.analyzer[-1], '--epilogue')
        self.assertEqual(returned.analyzer.count('--epilogue'), 1)
        self.assertEqual(returned.observers[-3][1], 'prepare_v920_handler_return.py')
        self.assertEqual(returned.observers[-2][1], 'prepare_v922_windows_scheduler_entry.py')
        self.assertEqual(returned.observers[-1][1], 'prepare_v923_windows_scheduler_return.py')

    def test_original_code_mapping_excludes_fixture_guard(self):
        j, d, r = 0x80526ca8, 0x805265ac, 0x805265d4
        blr = 0x4e800020
        roots = {
            j: [0x48000001, 0x48000001, 0x7ca30378, 0x48000001, blr],
            E: [0x60000000] * 14 + [blr],
            S: [0x60000000] * 5 + [blr],
            d: [blr], r: [blr], L: [blr] * 53 + [RFI],
        }
        expected = native_expectations(roots, j, d, r)
        for pc in (j, j+4, j+8, j+12, E, S, d, r, L, L+53*4):
            self.assertIn(pc, expected)
        self.assertEqual(expected[j][0], DISPATCH)
        self.assertEqual(expected[L+53*4], (L, RFI))
        self.assertNotIn(j+16, expected)
        self.assertEqual(len(expected), 4+15+6+1+1+54)
        roots[L][-1] = blr
        with self.assertRaises(ValueError):
            native_expectations(roots, j, d, r)

    def test_refusals_never_expose_owner_values(self):
        for message, code in (('native IPC label identity', 'label'),
                              ('native IPC label body', 'fallback'),
                              ('native overlap', 'overlap'),
                              ('native IPC coverage', 'coverage'),
                              ('owner code at 0x80529434', 'private_or_io')):
            self.assertEqual(refusal_reason(ValueError(message)), code)

    def test_missing_original_owner_fails_closed(self):
        from pathlib import Path
        with self.assertRaises((ValueError, OSError)):
            audit(b'', b'', Path('/nonexistent/owner-private-image'))


if __name__ == '__main__':
    unittest.main()
