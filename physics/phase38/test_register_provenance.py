"""Phase 38 synthetic source-only tests; no copyrighted binaries required."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register_provenance import (
    basic_block_starts, decode_gpr_effect, fields, is_control_transfer,
    transfer_target, report_from_verified_words, trace_register, main,
)


def itype(op, rs, rt, imm):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xffff)


def rtype(rs, rt, rd, funct):
    return (rs << 21) | (rt << 16) | (rd << 11) | funct


def row(pc, base, displacement, evidence='', mnemonic='lwc1', direction='read'):
    return {'pc': f'0x{pc:08X}', 'signed_displacement': displacement,
            'base_register': f'r{base}', 'evidence_label': evidence,
            'direction': direction, 'mnemonic': mnemonic}


class DecodeTests(unittest.TestCase):
    def test_signed_imm(self):
        self.assertEqual(fields(itype(9, 2, 3, -123))[-1], -123)

    def test_lui_definition(self):
        self.assertEqual(decode_gpr_effect(itype(15, 0, 8, 0x1234)),
                         ('lui', 8, (), 0x1234))

    def test_addiu_definition(self):
        self.assertEqual(decode_gpr_effect(itype(9, 8, 8, -4)),
                         ('addiu', 8, (8,), -4))

    def test_ori_definition(self):
        self.assertEqual(decode_gpr_effect(itype(13, 8, 8, 0x9876)),
                         ('ori', 8, (8,), 0x9876))

    def test_memory_load_gpr_definition(self):
        self.assertEqual(decode_gpr_effect(itype(0x23, 4, 16, 0x30)),
                         ('load', 16, (4,), 0x30))

    def test_float_load_not_gpr_definition(self):
        self.assertEqual(decode_gpr_effect(itype(0x31, 4, 16, 0x8c))[0],
                         'no_gpr_write')

    def test_float_store_not_gpr_definition(self):
        self.assertEqual(decode_gpr_effect(itype(0x39, 4, 16, 0x8c))[0],
                         'no_gpr_write')

    def test_move_addu_zero(self):
        self.assertEqual(decode_gpr_effect(rtype(4, 0, 16, 0x21)),
                         ('move', 16, (4,), 0))

    def test_move_or_zero(self):
        self.assertEqual(decode_gpr_effect(rtype(0, 16, 18, 0x25)),
                         ('move', 18, (16,), 0))

    def test_addu_two_registers(self):
        self.assertEqual(decode_gpr_effect(rtype(8, 9, 10, 0x21)),
                         ('binary', 10, (8, 9), 0))

    def test_unknown_gpr_definition(self):
        self.assertEqual(decode_gpr_effect(itype(12, 4, 4, 0xff))[0],
                         'unknown_definition')

    def test_opaque_opcode(self):
        self.assertEqual(decode_gpr_effect(0x70000002)[0], 'opaque')

    def test_lwl_lwr_are_partial_definitions(self):
        for opcode in (0x22, 0x26):
            with self.subTest(opcode=opcode):
                self.assertEqual(decode_gpr_effect(itype(opcode, 4, 18, 0x20))[0],
                                 'partial_load_unknown')

    def test_partial_load_cannot_claim_pointer_origin(self):
        words = [itype(0x23, 4, 18, 0x10), itype(0x22, 4, 18, 0x20),
                 itype(0x31, 18, 3, 0x48)]
        self.assertEqual(trace_register(words, 0x1000, 0, 2, 18)['kind'],
                         'partial_load_unknown')

    def test_zero_nop(self):
        self.assertEqual(decode_gpr_effect(0)[0], 'no_gpr_write')

    def test_jal_is_control(self):
        self.assertTrue(is_control_transfer(0x0c000000))

    def test_conditional_branch_target(self):
        self.assertEqual(transfer_target(itype(4, 3, 4, -2), 0x1008), 0x1004)

    def test_j_target_region(self):
        w = (2 << 26) | (0x00001234 >> 2)
        self.assertEqual(transfer_target(w, 0x10000000), 0x10001234)


class BoundaryTests(unittest.TestCase):
    def test_control_adds_delay_and_fallthrough(self):
        words = [itype(4, 2, 3, 2), 0, 0, 0, 0]
        self.assertEqual(basic_block_starts(words, 0x1000), [0, 1, 2, 3])

    def test_indirect_jr_boundary(self):
        words = [rtype(31, 0, 0, 8), 0, 0]
        self.assertEqual(basic_block_starts(words, 0x1000), [0, 1, 2])

    def test_no_branch_single_block(self):
        self.assertEqual(basic_block_starts([0, 0], 0x1000), [0])

    def test_bad_alignment_rejected(self):
        with self.assertRaises(ValueError):
            basic_block_starts([0], 0x1001)

    def test_invalid_word_rejected(self):
        with self.assertRaises(ValueError):
            basic_block_starts([-1], 0x1000)


class TraceTests(unittest.TestCase):
    def test_lui_ori_chain(self):
        words = [itype(15, 0, 8, 0x1234), itype(13, 8, 8, 0x5678),
                 itype(0x31, 8, 1, 0x8c)]
        trace = trace_register(words, 0x1000, 0, 2, 8)
        self.assertEqual(trace['kind'], 'ori')
        self.assertEqual(trace['source']['kind'], 'lui')

    def test_load_pointer_chain(self):
        words = [itype(0x23, 4, 18, 0x20), itype(0x31, 18, 2, 0x48)]
        trace = trace_register(words, 0x1000, 0, 1, 18)
        self.assertEqual(trace['kind'], 'load')
        self.assertEqual(trace['displacement'], 0x20)
        self.assertEqual(trace['address_base']['kind'], 'block_live_in_unknown')

    def test_moves_chain(self):
        words = [itype(0x23, 4, 16, 0x20), rtype(16, 0, 19, 0x21),
                 itype(0x39, 19, 1, 0x188)]
        trace = trace_register(words, 0x1000, 0, 2, 19)
        self.assertEqual(trace['source']['kind'], 'load')

    def test_prevents_crossing_prior_block(self):
        words = [itype(0x23, 4, 18, 0x20), 0, itype(0x31, 18, 2, 0x48)]
        self.assertEqual(trace_register(words, 0x1000, 2, 2, 18)['kind'],
                         'block_live_in_unknown')

    def test_opaque_barrier(self):
        words = [itype(0x23, 4, 18, 0x20), 0x70000002,
                 itype(0x31, 18, 2, 0x48)]
        self.assertEqual(trace_register(words, 0x1000, 0, 2, 18)['kind'],
                         'opaque_barrier')

    def test_unknown_clobber_not_previous_load(self):
        words = [itype(0x23, 4, 18, 0x20), itype(12, 18, 18, 0x10),
                 itype(0x31, 18, 2, 0x48)]
        self.assertEqual(trace_register(words, 0x1000, 0, 2, 18)['kind'],
                         'unknown_definition')

    def test_zero_architectural(self):
        self.assertEqual(trace_register([0], 0x1000, 0, 0, 0)['kind'],
                         'architectural_zero')

    def test_invalid_trace_arguments(self):
        with self.assertRaises(ValueError):
            trace_register([0], 0x1000, 0, 1, 32)

    def test_depth_limit(self):
        words = [itype(15, 0, 8, 0x12), itype(9, 8, 9, 4),
                 itype(9, 9, 10, 4), itype(0x31, 10, 1, 0x48)]
        self.assertEqual(trace_register(words, 0x1000, 0, 3, 10, max_depth=2)
                         ['source']['source']['kind'], 'depth_limit')

    def test_store_is_not_gpr_definition(self):
        words = [itype(0x23, 4, 18, 0x20), itype(0x39, 18, 2, 0x48),
                 itype(0x31, 18, 3, 0x64)]
        self.assertEqual(trace_register(words, 0x1000, 0, 2, 18)['kind'], 'load')


class ReportTests(unittest.TestCase):
    def test_candidate_annotated(self):
        words = [itype(0x23, 4, 18, 0x20), itype(0x31, 18, 1, 0x48)]
        rep = report_from_verified_words('synthetic', 'fixture', 0x1000, words,
                                         [row(0x1004, 18, 0x48)])
        self.assertEqual(rep['candidate_accesses'][0]['base_provenance']['kind'], 'load')

    def test_no_candidate_ignored(self):
        words = [itype(0x31, 18, 1, 0x70)]
        rep = report_from_verified_words('synthetic', 'fixture', 0x1000, words,
                                         [row(0x1000, 18, 0x70)])
        self.assertEqual(rep['candidate_access_count'], 0)

    def test_anchor_included_even_non_candidate(self):
        words = [itype(0x31, 18, 1, 0x70)]
        rep = report_from_verified_words('synthetic', 'fixture', 0x1000, words,
                                         [row(0x1000, 18, 0x70, 'evidence')])
        self.assertEqual(rep['candidate_access_count'], 1)

    def test_phase36_displacement_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            report_from_verified_words('x', 'fake', 0x1000,
                                      [itype(0x31, 18, 1, 0x48)],
                                      [row(0x1000, 18, 0x64)])

    def test_phase36_register_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            report_from_verified_words('x', 'fake', 0x1000,
                                      [itype(0x31, 18, 1, 0x48)],
                                      [row(0x1000, 4, 0x48)])

    def test_phase36_pc_out_of_bounds_rejected(self):
        with self.assertRaises(ValueError):
            report_from_verified_words('x', 'fake', 0x1000,
                                      [itype(0x31, 18, 1, 0x48)],
                                      [row(0x2000, 18, 0x48)])

    def test_cli_bad_sources_fail_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / 'unsupported.elf'
            output = Path(d) / 'report.json'
            bad.write_bytes(b'not a supported PS2 binary')
            with patch('register_provenance.audit_source_file', side_effect=ValueError('unsupported SHA')):
                with self.assertRaises(SystemExit) as exc:
                    main(['--uc', str(bad), '--carbon', str(bad), '--output', str(output)])
            self.assertEqual(exc.exception.code, 1)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
