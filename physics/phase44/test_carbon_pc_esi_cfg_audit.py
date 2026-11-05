"""Phase 44 synthetic CFG regression tests. No user game binaries."""
from __future__ import annotations

import io
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carbon_pc_esi_cfg_audit as p44
from physics.phase42.carbon_pc_esi_access_census import find_accesses
from physics.phase43.carbon_pc_candidate_access_review import build_review


def ins(pc, blob, mnemonic, operands=''):
    return {'pc': pc, 'length': len(blob), 'bytes': blob, 'mnemonic': mnemonic,
            'operands': operands}


def store(pc=0x1000):
    return ins(pc, bytes.fromhex('898604010000'), 'mov',
               'DWORD PTR [esi+0x104],eax')


def load(pc=0x1006):
    return ins(pc, bytes.fromhex('8b8604010000'), 'mov',
               'eax,DWORD PTR [esi+0x104]')


def write118(pc=0x100c):
    return ins(pc, bytes.fromhex('899618010000'), 'mov',
               'DWORD PTR [esi+0x118],edx')


def straight():
    return [store(), load(), write118()]


def synthetic_census(rows):
    data = find_accesses(rows)
    return {'source_sha256': 'SYNTHETIC_ONLY',
            'simple_esi_accesses': data['simple_esi_accesses'],
            'simple_esi_access_count': data['simple_esi_access_count'],
            'complex_esi_operand_count': data['complex_esi_operand_count']}


class ControlFlowTests(unittest.TestCase):
    def test_straightline_cfg(self):
        cfg = p44.build_cfg(straight())
        self.assertEqual(cfg['edges'][0x1000], (0x1006,))
        self.assertEqual(cfg['edges'][0x1006], (0x100c,))

    def test_no_edge_after_last_instruction(self):
        cfg = p44.build_cfg(straight())
        self.assertEqual(cfg['edges'][0x100c], ())

    def test_direct_conditional_branch_and_fallthrough(self):
        rows = [store(), ins(0x1006, b'\x74\x02', 'je', '0x100a'),
                ins(0x1008, b'\x89\xfe', 'mov', 'esi,edi'),
                load(0x100a)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], (0x100a, 0x1008))

    def test_unconditional_direct_jump_excludes_fallthrough(self):
        rows = [store(), ins(0x1006, b'\xeb\x02', 'jmp', '0x100a'),
                ins(0x1008, b'\x89\xfe', 'mov', 'esi,edi'),
                load(0x100a)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], (0x100a,))

    def test_jump_into_middle_rejected(self):
        rows = [store(), ins(0x1006, b'\xeb\x01', 'jmp', '0x1009'),
                load(0x1008)]
        with self.assertRaisesRegex(ValueError, 'middle'):
            p44.build_cfg(rows)

    def test_jump_leaving_function(self):
        rows = [store(), ins(0x1006, b'\xeb\x7f', 'jmp', '0x1087'),
                load(0x1008)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], ())
        self.assertEqual(cfg['issues'][0x1006], 'branch_exits_function')

    def test_indirect_jump_unresolved(self):
        rows = [store(), ins(0x1006, b'\xff\xe0', 'jmp', 'eax'),
                load(0x1008)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], ())
        self.assertEqual(cfg['issues'][0x1006], 'unresolved_branch_target')

    def test_indirect_conditional_keeps_known_fallthrough(self):
        rows = [store(), ins(0x1006, b'\x74\x02', 'je', 'DWORD PTR [esi]'),
                load(0x1008)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], (0x1008,))
        self.assertEqual(cfg['issues'][0x1006], 'unresolved_branch_target')

    def test_return_terminates(self):
        rows = [store(), ins(0x1006, b'\xc3', 'ret'),
                load(0x1007)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], ())
        self.assertEqual(cfg['issues'][0x1006], 'terminal_exit')

    def test_call_continues_with_hazard(self):
        rows = [store(), ins(0x1006, b'\xe8\x00\x00\x00\x00', 'call', '0x100b'),
                load(0x100b)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['edges'][0x1006], (0x100b,))
        self.assertEqual(cfg['issues'][0x1006], 'call_unmodeled_effect')

    def test_unsupported_branch_does_not_invent_edge(self):
        rows = [store(), ins(0x1006, b'\xe3\x02', 'jrcxz', '0x100a'),
                load(0x1008)]
        cfg = p44.build_cfg(rows)
        self.assertEqual(cfg['issues'][0x1006], 'unsupported_control_transfer')
        self.assertEqual(cfg['edges'][0x1006], ())

    def test_empty_instruction_list_rejected(self):
        with self.assertRaises(ValueError):
            p44.build_cfg([])

    def test_noncontiguous_rejected(self):
        with self.assertRaises(ValueError):
            p44.build_cfg([store(), load(0x1007)])

    def test_objdump_synthetic_branch_targets(self):
        decoded = p44.disassemble(bytes.fromhex(
            '898604010000740289fe8b8604010000'), 0x1000)
        cfg = p44.build_cfg(decoded)
        self.assertEqual(cfg['edges'][0x1006], (0x100a, 0x1008))


class EffectTests(unittest.TestCase):
    def test_no_write_stable(self):
        self.assertEqual(p44.apply_effect(p44.UNCHANGED, 'skip_no_target_write'), p44.UNCHANGED)

    def test_copy_is_write(self):
        self.assertEqual(p44.apply_effect(p44.UNCHANGED, 'register_copy'), p44.REDEFINED)

    def test_memory_load_is_definition(self):
        self.assertEqual(p44.apply_effect(p44.UNCHANGED, 'memory_load_unknown_value'), p44.REDEFINED)

    def test_opaque_instruction_taints(self):
        self.assertEqual(p44.apply_effect(p44.UNCHANGED, 'opaque_barrier'), p44.UNKNOWN)

    def test_uncertainty_not_healed_by_move(self):
        self.assertEqual(p44.apply_effect(p44.UNKNOWN, 'register_copy'), p44.UNKNOWN)

    def test_detected_definition_not_healed_by_nop(self):
        self.assertEqual(p44.apply_effect(p44.REDEFINED, 'skip_no_gpr_write'), p44.REDEFINED)

    def test_partial_register_unknown(self):
        self.assertEqual(p44.apply_effect(p44.UNCHANGED,
                         'partial_register_write_unknown'), p44.UNKNOWN)

    def test_invalid_state_fails(self):
        with self.assertRaises(ValueError):
            p44.apply_effect('imaginary', 'register_copy')


class PathsTests(unittest.TestCase):
    def test_straightline_clean(self):
        result = p44.audit_paths(p44.build_cfg(straight()), 0x1000, 0x1006)
        self.assertTrue(result['route_with_no_detected_esi_write'])
        self.assertFalse(result['same_runtime_object_proven'])

    def test_branch_both_clean_and_redefined(self):
        rows = [store(), ins(0x1006, b'\x74\x02', 'je', '0x100a'),
                ins(0x1008, b'\x89\xfe', 'mov', 'esi,edi'),
                load(0x100a)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x100a)
        self.assertEqual(set(result['modeled_target_states']),
                         {p44.UNCHANGED, p44.REDEFINED})

    def test_unconditional_jump_skips_esi_write(self):
        rows = [store(), ins(0x1006, b'\xeb\x02', 'jmp', '0x100a'),
                ins(0x1008, b'\x89\xfe', 'mov', 'esi,edi'),
                load(0x100a)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x100a)
        self.assertEqual(result['modeled_target_states'], [p44.UNCHANGED])

    def test_first_memory_access_redefines_esi(self):
        rows = [ins(0x1000, bytes.fromhex('8bb604010000'), 'mov',
                    'esi,DWORD PTR [esi+0x104]'), load(0x1006)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x1006)
        self.assertEqual(result['modeled_target_states'], [p44.REDEFINED])

    def test_opaque_effect_changes_to_unknown(self):
        rows = [store(), ins(0x1006, b'\x87\xfe', 'xchg', 'esi,edi'),
                load(0x1008)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x1008)
        self.assertEqual(result['modeled_target_states'], [p44.UNKNOWN])

    def test_call_taints_esi(self):
        rows = [store(), ins(0x1006, b'\xe8\x00\x00\x00\x00', 'call', '0x100b'),
                load(0x100b)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x100b)
        self.assertTrue(result['route_with_uncertain_esi_effect'])
        self.assertIn('call_unmodeled_effect', result['unresolved_or_exiting_controls_encountered'])

    def test_no_route_after_return(self):
        rows = [store(), ins(0x1006, b'\xc3', 'ret'), load(0x1007)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x1007)
        self.assertFalse(result['modeled_routes_to_target'])
        self.assertIn('terminal_exit', result['unresolved_or_exiting_controls_encountered'])

    def test_indirect_jump_unresolved(self):
        rows = [store(), ins(0x1006, b'\xff\xe0', 'jmp', 'eax'), load(0x1008)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x1008)
        self.assertFalse(result['modeled_routes_to_target'])
        self.assertIn('unresolved_branch_target', result['unresolved_or_exiting_controls_encountered'])

    def test_backward_loop_terminates(self):
        rows = [store(), ins(0x1006, b'\x75\xfe', 'jne', '0x1006'), load(0x1008)]
        result = p44.audit_paths(p44.build_cfg(rows), 0x1000, 0x1008)
        self.assertTrue(result['modeled_routes_to_target'])
        self.assertLessEqual(result['explored_static_states'], 3 * len(rows))

    def test_source_and_target_must_be_decoded(self):
        with self.assertRaises(ValueError):
            p44.audit_paths(p44.build_cfg(straight()), 0x1001, 0x1006)
        with self.assertRaises(ValueError):
            p44.audit_paths(p44.build_cfg(straight()), 0x100c, 0x1000)


class ReportTests(unittest.TestCase):
    def test_phase43_review_is_augmented(self):
        rows = straight()
        review = build_review(rows, synthetic_census(rows),
                              anchors=(0x1000, 0x100c))
        with patch.object(p44, 'ANCHOR_ADDRESSES', (0x1000, 0x100c)):
            out = p44.augment_review(rows, review)
        self.assertEqual(out['phase'], 44)
        pair = out['candidate_offsets'][0]['consecutive_same_offset_spans'][0]
        self.assertTrue(pair['cfg_path_evidence']['route_with_no_detected_esi_write'])
        self.assertFalse(out['runtime_object_identity_verified'])
        self.assertFalse(out['gameplay_patch_created'])

    def test_no_original_binary_accepted(self):
        with self.assertRaises(ValueError):
            p44.audit_verified_image(b'not the supported Carbon PC build')

    def test_failed_cli_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'NFSC.exe'
            output = Path(directory) / 'report.json'
            source.write_bytes(b'invalid binary')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                p44.main([str(source), '--output', str(output)])
            self.assertEqual(err.exception.code, 1)
            self.assertFalse(output.exists())

    def test_gate_failure_does_not_call_disassembler(self):
        with patch.object(p44, 'audit_verified_pc', side_effect=ValueError('bad SHA')), \
                patch.object(p44, 'disassemble') as runner:
            with self.assertRaisesRegex(ValueError, 'bad SHA'):
                p44.audit_verified_image(b'invalid')
            runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
