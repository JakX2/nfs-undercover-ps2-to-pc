"""Synthetic x86 provenance tests. No game executable or extracted code included."""
from __future__ import annotations

import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carbon_pc_register_trace as phase41


def inst(pc, raw, mnemonic, ops=''):
    return {'pc': pc, 'length': len(raw), 'bytes': raw,
            'mnemonic': mnemonic, 'operands': ops}


def sample():
    return [
        inst(0x1000, bytes.fromhex('b834120000'), 'mov', 'eax,0x1234'),
        inst(0x1005, bytes.fromhex('89c2'), 'mov', 'edx,eax'),
        inst(0x1007, bytes.fromhex('898604010000'), 'mov', 'DWORD PTR [esi+0x104],eax'),
        inst(0x100d, bytes.fromhex('90'), 'nop'),
        inst(0x100e, bytes.fromhex('899618010000'), 'mov', 'DWORD PTR [esi+0x118],edx'),
    ]


class BinutilsTests(unittest.TestCase):
    def test_real_objdump_round_trip(self):
        raw = b''.join(x['bytes'] for x in sample())
        rows = phase41.disassemble(raw, 0x1000)
        self.assertEqual([x['pc'] for x in rows], [x['pc'] for x in sample()])
        self.assertEqual(rows[2]['mnemonic'], 'mov')
        self.assertIn('esi+0x104', rows[2]['operands'])

    def test_real_objdump_with_branch(self):
        rows = phase41.disassemble(bytes.fromhex('eb019090c3'), 0x2000)
        self.assertTrue(rows[0]['mnemonic'].startswith('j'))
        self.assertEqual(rows[-1]['mnemonic'], 'ret')

    def test_disassembler_missing_rejected(self):
        with patch.object(phase41.shutil, 'which', return_value=None):
            with self.assertRaises(RuntimeError):
                phase41.disassemble(b'\x90', 0x1000)

    def test_disassembler_size_limit(self):
        with self.assertRaises(ValueError):
            phase41.disassemble(b'\x90' * 4097, 0x1000)

    def test_parse_rejects_missing_instruction(self):
        with self.assertRaises(ValueError):
            phase41.parse_objdump('', b'\x90', 0x1000)

    def test_parse_rejects_wrong_bytes(self):
        stdout = ' 1000:\t90 \tnop\n'
        with self.assertRaises(ValueError):
            phase41.parse_objdump(stdout, b'\xc3', 0x1000)

    def test_parse_rejects_gap(self):
        stdout = ' 1001:\t90 \tnop\n'
        with self.assertRaises(ValueError):
            phase41.parse_objdump(stdout, b'\x90', 0x1000)

    def test_parse_rejects_bad(self):
        stdout = ' 1000:\t90 \t(bad)\n'
        with self.assertRaises(ValueError):
            phase41.parse_objdump(stdout, b'\x90', 0x1000)


class OperandTests(unittest.TestCase):
    def test_register_family(self):
        self.assertEqual(phase41.root_register('al'), ('eax', False))
        self.assertEqual(phase41.root_register('eax'), ('eax', True))
        self.assertEqual(phase41.root_register('esp'), ('esp', True))

    def test_split_bracketed_operands(self):
        self.assertEqual(phase41.split_operands('DWORD PTR [esi+ecx*4+0x10],eax'),
                         ['dword ptr [esi+ecx*4+0x10]', 'eax'])

    def test_split_invalid_brackets(self):
        with self.assertRaises(ValueError):
            phase41.split_operands('eax,[esi')

    def test_clobber_partial_register(self):
        r = inst(0x1000, b'\xb0\x01', 'mov', 'al,0x1')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'],
                         'partial_register_write_unknown')

    def test_independent_memory_store_does_not_clobber(self):
        r = inst(0x1000, b'\x89\x06', 'mov', 'DWORD PTR [esi],eax')
        self.assertEqual(phase41.describe_effect(r, 'edx')['kind'],
                         'skip_no_target_write')

    def test_known_zero(self):
        r = inst(0x1000, b'\x31\xc0', 'xor', 'eax,eax')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'], 'known_zero')

    def test_immediate(self):
        r = inst(0x1000, bytes.fromhex('b834120000'), 'mov', 'eax,0x1234')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'], 'immediate_or_symbol')

    def test_load_from_memory_stops(self):
        r = inst(0x1000, b'\x8b\x06', 'mov', 'eax,DWORD PTR [esi]')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'], 'memory_load_unknown_value')

    def test_unknown_instruction_stops(self):
        r = inst(0x1000, b'\x87\xc2', 'xchg', 'edx,eax')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'], 'opaque_barrier')

    def test_arithmetic_stops(self):
        r = inst(0x1000, b'\x01\xd0', 'add', 'eax,edx')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'],
                         'arithmetic_definition_unresolved')

    def test_cmp_safe_to_skip(self):
        r = inst(0x1000, b'\x39\xd0', 'cmp', 'eax,edx')
        self.assertEqual(phase41.describe_effect(r, 'eax')['kind'],
                         'skip_no_gpr_write')

    def test_one_operand_imul_clobbers_implicit_edx_eax(self):
        r = inst(0x1000, b'\xf7\xeb', 'imul', 'ebx')
        for register in ('eax', 'edx'):
            with self.subTest(register=register):
                self.assertEqual(phase41.describe_effect(r, register)['kind'],
                                 'implicit_register_definition_unknown')

    def test_two_operand_imul_does_not_implicitly_write_edx(self):
        r = inst(0x1000, b'\x0f\xaf\xc3', 'imul', 'eax,ebx')
        self.assertEqual(phase41.describe_effect(r, 'edx')['kind'],
                         'skip_no_target_write')

    def test_pop_updates_esp_even_when_destination_is_other_register(self):
        r = inst(0x1000, b'\x58', 'pop', 'eax')
        self.assertEqual(phase41.describe_effect(r, 'esp')['kind'],
                         'implicit_register_definition_unknown')


    def test_call_classified_as_control(self):
        self.assertTrue(phase41.transfer_kind('call'))
        self.assertTrue(phase41.transfer_kind('jne'))
        self.assertFalse(phase41.transfer_kind('mov'))


class TraceTests(unittest.TestCase):
    def test_trace_first_store_to_immediate(self):
        trace = phase41.trace_before(sample(), 0x1007, 'eax')
        self.assertEqual(trace['status'], 'immediate_or_symbol')

    def test_trace_second_store_through_register_copy(self):
        trace = phase41.trace_before(sample(), 0x100e, 'edx')
        self.assertEqual(trace['status'], 'immediate_or_symbol')
        self.assertEqual(trace['evidence'][0]['effect']['kind'], 'register_copy')

    def test_trace_unknown_live_in(self):
        trace = phase41.trace_before([sample()[2]], 0x1007, 'eax')
        self.assertEqual(trace['status'], 'block_live_in_unknown')

    def test_branch_barrier(self):
        rows = [
            inst(0x1000, b'\xb8\x01\x00\x00\x00', 'mov', 'eax,0x1'),
            inst(0x1005, b'\x74\x01', 'je', '0x1008'),
            inst(0x1007, b'\x90', 'nop'),
            inst(0x1008, bytes.fromhex('898604010000'), 'mov', 'DWORD PTR [esi+0x104],eax'),
        ]
        self.assertEqual(phase41.trace_before(rows, 0x1008, 'eax')['status'],
                         'block_live_in_unknown')

    def test_branch_into_middle_instruction_rejected(self):
        rows = [
            inst(0x1000, b'\xeb\x02', 'jmp', '0x1004'),
            inst(0x1002, b'\xb8\x01\x00\x00\x00', 'mov', 'eax,0x1'),
        ]
        with self.assertRaises(ValueError):
            phase41.boundaries(rows)

    def test_opaque_barrier(self):
        rows = [
            inst(0x1000, b'\xb8\x01\x00\x00\x00', 'mov', 'eax,0x1'),
            inst(0x1005, b'\x87\xc2', 'xchg', 'eax,edx'),
            inst(0x1007, bytes.fromhex('898604010000'), 'mov', 'DWORD PTR [esi+0x104],eax'),
        ]
        self.assertEqual(phase41.trace_before(rows, 0x1007, 'eax')['status'],
                         'opaque_barrier')

    def test_step_limit(self):
        rows = [inst(0x1000, b'\x90', 'nop'), sample()[2]]
        self.assertEqual(phase41.trace_before(rows, 0x1007, 'eax', 0)['status'],
                         'step_limit')

    def test_invalid_anchor_or_register(self):
        with self.assertRaises(ValueError):
            phase41.trace_before(sample(), 0x1234, 'eax')
        with self.assertRaises(ValueError):
            phase41.trace_before(sample(), 0x1007, 'r12')


class EndToEndTests(unittest.TestCase):
    def test_invalid_exe_fails_without_creating_report(self):
        with tempfile.TemporaryDirectory() as d:
            src, report = Path(d) / 'NFSC.exe', Path(d) / 'report.json'
            src.write_bytes(b'not a game executable')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                phase41.main([str(src), '--output', str(report)])
            self.assertFalse(report.exists())

    def test_known_anchor_decode_matches_phase40(self):
        for pc in phase41.ANCHOR_ADDRESSES:
            row = phase41.decode_mov_store(bytes.fromhex(phase41.BYTES[pc]), pc)
            self.assertEqual(row['base_register'], 'esi')
            self.assertIn(row['source_register'], ('eax', 'edx'))

    def test_unmodified_real_verifier_rejects_fake(self):
        with self.assertRaises(ValueError):
            phase41.analyze_verified_image(b'bad executable')

    def test_source_binaries_not_exported_by_reports(self):
        rows = sample()
        traces = [phase41.trace_before(rows, 0x1007, 'eax'),
                  phase41.trace_before(rows, 0x100e, 'edx')]
        self.assertTrue(all('evidence' in r for r in traces))
        self.assertNotIn('raw_binary', str(traces))


if __name__ == '__main__':
    unittest.main()
