"""Phase46 tests use synthetic JSON only; no proprietary game files."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_evidence_bundle as p46


def path(a, b, states=('no_detected_esi_write',), issues=()):
    states = list(states)
    return {
        'earlier_pc': a, 'later_pc': b,
        'modeled_routes_to_target': bool(states),
        'modeled_target_states': states,
        'route_with_no_detected_esi_write': 'no_detected_esi_write' in states,
        'route_with_esi_definition': 'esi_definition_seen' in states,
        'route_with_uncertain_esi_effect': 'unknown_esi_effect' in states,
        'unresolved_or_exiting_controls_encountered': list(issues),
        'explored_static_states': 3, 'same_runtime_object_proven': False,
        'real_execution_observed': False,
    }


def fixture():
    candidates = []
    summary = []
    for offset, pc, _ in p46.EXPECTED:
        firstpc = '0x006EF7B3' if offset == 0x104 else pc
        directions = ['read', 'write'] if offset == 0x104 else ['write']
        pcs = [firstpc, pc] if offset == 0x104 else [pc]
        accesses = [
            {'pc': here, 'mnemonic': 'mov', 'direction': direction,
             'known_phase40_anchor': here == pc}
            for here, direction in zip(pcs, directions)
        ]
        spans = [
            {'earlier_pc': pcs[0], 'later_pc': pcs[1],
             'static_span': {'status': 'no_detected_esi_write_in_same_linear_region'},
             'cfg_path_evidence': path(pcs[0], pcs[1])}
        ] if len(pcs) > 1 else []
        candidates.append({
            'signed_displacement': offset, 'known_store_pc': pc,
            'static_read_occurrences': int('read' in directions),
            'static_write_occurrences': 1, 'unknown_direction_occurrences': 0,
            'accesses': accesses, 'consecutive_same_offset_spans': spans,
            'static_read_and_write_shapes_both_present': 'read' in directions,
        })
        summary.append({
            'candidate_offset': offset, 'classification': 'syntactic_esi_relative_memory_operand',
            'static_read_occurrences': int('read' in directions),
            'static_write_occurrences': 1, 'unknown_direction_occurrences': 0,
            'known_store_pc': pc, 'candidate_access_pcs': pcs,
            'modeled_inter_access_paths': len(spans), 'semantic_role': 'unverified',
            'matching_ps2_offset': None,
        })
    return {
        'phase': 45, 'schema_version': 1,
        'source': {'platform': 'Carbon PC', 'sha256': p46.SUPPORTED_SHA256,
                   'steering_function_va': '0x006EF540', 'verified_phase31_checks': 17,
                   'function_length_bytes': 729},
        'verification': {
            'phase31_sha_and_anchor_gate': 'enforced_by_real_cli',
            'known_store_instruction_boundaries_checked': True,
            'complete_function_instruction_coverage_checked': True,
            'source_binary_embedded_in_report': False,
            'ps2_to_pc_field_equivalence_verified': False,
            'runtime_gameplay_execution_observed': False,
            'steering_handling_patch_produced': False,
        },
        'overview': {
            'decoded_function_instructions': 150,
            'known_store_anchor_count': 2,
            'simple_esi_memory_access_count': 4,
            'complex_esi_operand_count': 0,
            'unparsed_memory_operand_form_count': 0,
            'candidate_offsets': summary,
        },
        'register_origin_evidence': [
            {'instruction_pc': pc, 'syntactic_destination': f'[esi+0x{offset:x}]',
             'source_register': reg, 'field_semantics': 'unknown',
             'source_register_local_trace': {'status': 'block_live_in_unknown', 'evidence': []}}
            for offset, pc, reg in p46.EXPECTED
        ],
        'candidate_path_evidence': {
            'anchor_to_anchor': path('0x006EF7B9', '0x006EF7C0'),
            'candidates': candidates, 'cfg_issue_counts': {},
        },
        'unresolved_address_forms': {
            'complex_esi_operands': [], 'unparsed_memory_operand_forms': [],
        },
    }


class ValidationTests(unittest.TestCase):
    def test_fixture_valid(self):
        result = p46.validate_bundle(fixture())
        self.assertEqual([(r['offset'], r['reads'], r['writes']) for r in result],
                         [(0x104, 1, 1), (0x118, 0, 1)])

    def test_only_phase45(self):
        r = fixture(); r['phase'] = 44
        with self.assertRaisesRegex(ValueError, 'Phase45'):
            p46.validate_bundle(r)

    def test_unsupported_sha_rejected(self):
        r = fixture(); r['source']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA'):
            p46.validate_bundle(r)

    def test_bad_function_length(self):
        r = fixture(); r['source']['function_length_bytes'] = 728
        with self.assertRaisesRegex(ValueError, 'function length'):
            p46.validate_bundle(r)

    def test_boolean_as_integer_count_is_invalid(self):
        r = fixture(); r['overview']['decoded_function_instructions'] = True
        with self.assertRaisesRegex(ValueError, 'nonnegative'):
            p46.validate_bundle(r)

    def test_embedded_binary_claim_rejected(self):
        r = fixture(); r['verification']['source_binary_embedded_in_report'] = True
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_ps2_mapping_claim_rejected(self):
        r = fixture(); r['verification']['ps2_to_pc_field_equivalence_verified'] = True
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_runtime_claim_rejected(self):
        r = fixture(); r['verification']['runtime_gameplay_execution_observed'] = True
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_register_mismatch_rejected(self):
        r = fixture(); r['register_origin_evidence'][1]['source_register'] = 'eax'
        with self.assertRaisesRegex(ValueError, 'register'):
            p46.validate_bundle(r)

    def test_store_pc_mismatch_rejected(self):
        r = fixture(); r['overview']['candidate_offsets'][0]['known_store_pc'] = '0x006EF7C0'
        with self.assertRaisesRegex(ValueError, 'anchor'):
            p46.validate_bundle(r)

    def test_field_name_claim_rejected(self):
        r = fixture(); r['overview']['candidate_offsets'][0]['semantic_role'] = 'steering-angle'
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_candidate_source_ps2_mapping_rejected(self):
        r = fixture(); r['overview']['candidate_offsets'][1]['matching_ps2_offset'] = 0x188
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_access_count_disagreement_rejected(self):
        r = fixture(); r['overview']['candidate_offsets'][0]['static_read_occurrences'] = 2
        with self.assertRaisesRegex(ValueError, 'read count'):
            p46.validate_bundle(r)

    def test_unknown_direction_count_disagreement(self):
        r = fixture(); r['candidate_path_evidence']['candidates'][0]['unknown_direction_occurrences'] = 1
        with self.assertRaisesRegex(ValueError, 'unknown direction'):
            p46.validate_bundle(r)

    def test_duplicate_candidate_pc_rejected(self):
        r = fixture(); r['candidate_path_evidence']['candidates'][0]['accesses'][0]['pc'] = '0x006EF7B9'
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            p46.validate_bundle(r)

    def test_missing_known_store_rejected(self):
        r = fixture(); r['candidate_path_evidence']['candidates'][0]['accesses'][1]['known_phase40_anchor'] = False
        with self.assertRaisesRegex(ValueError, 'anchor'):
            p46.validate_bundle(r)

    def test_span_count_mismatch_rejected(self):
        r = fixture(); r['overview']['candidate_offsets'][0]['modeled_inter_access_paths'] = 0
        with self.assertRaisesRegex(ValueError, 'span count'):
            p46.validate_bundle(r)

    def test_span_address_mismatch_rejected(self):
        r = fixture(); r['candidate_path_evidence']['candidates'][0]['consecutive_same_offset_spans'][0]['later_pc'] = '0x006EF7BF'
        with self.assertRaisesRegex(ValueError, 'span order'):
            p46.validate_bundle(r)

    def test_invalid_cfg_state_rejected(self):
        r = fixture(); r['candidate_path_evidence']['anchor_to_anchor']['modeled_target_states'] = ['real_steering']
        with self.assertRaisesRegex(ValueError, 'path states'):
            p46.validate_bundle(r)

    def test_cfg_boolean_disagrees_with_state(self):
        r = fixture(); r['candidate_path_evidence']['anchor_to_anchor']['route_with_no_detected_esi_write'] = False
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            p46.validate_bundle(r)

    def test_cfg_unverified_runtime_identity_required(self):
        r = fixture(); r['candidate_path_evidence']['anchor_to_anchor']['same_runtime_object_proven'] = True
        with self.assertRaisesRegex(ValueError, 'object identity'):
            p46.validate_bundle(r)

    def test_unknown_control_issue_marked(self):
        r = fixture(); r['candidate_path_evidence']['anchor_to_anchor']['unresolved_or_exiting_controls_encountered'] = ['indirect jmp']
        with self.assertRaisesRegex(ValueError, 'control labels'):
            p46.validate_bundle(r)

    def test_complex_count_disagrees(self):
        r = fixture(); r['overview']['complex_esi_operand_count'] = 2
        with self.assertRaisesRegex(ValueError, 'complex'):
            p46.validate_bundle(r)

    def test_candidates_cannot_exceed_full_census(self):
        r = fixture(); r['overview']['simple_esi_memory_access_count'] = 2
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            p46.validate_bundle(r)

    def test_invalid_address_cannot_be_markdown_injection(self):
        r = fixture(); r['register_origin_evidence'][0]['instruction_pc'] = '0x006EF7B9`|fake|'
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)

    def test_boolean_count_disallowed_in_cfg(self):
        r = fixture(); r['candidate_path_evidence']['cfg_issue_counts'] = {'unresolved': True}
        with self.assertRaises(ValueError):
            p46.validate_bundle(r)


class RenderingTests(unittest.TestCase):
    def test_unverified_review_banner(self):
        r = fixture(); s = p46.render_markdown(r, p46.validate_bundle(r), False)
        self.assertIn('NOT AUTHENTICATED', s)
        self.assertIn('self-declared', s)
        self.assertNotIn('Authenticated from source', s)

    def test_auth_banner_only_with_attestation(self):
        r = fixture(); s = p46.render_markdown(r, p46.validate_bundle(r), True)
        self.assertIn('Recomputed from the local exact original', s)
        self.assertNotIn('NOT AUTHENTICATED', s)

    def test_candidate_table_and_next_steps(self):
        r = fixture(); s = p46.render_markdown(r, p46.validate_bundle(r), False)
        self.assertIn('`+0x104`', s)
        self.assertIn('`+0x118`', s)
        self.assertIn('block_live_in_unknown', s)
        self.assertIn('indirect and complex', s)
        self.assertIn('reversible', s)

    def test_unknown_and_complex_findings(self):
        r = fixture()
        r['overview']['complex_esi_operand_count'] = 1
        r['unresolved_address_forms']['complex_esi_operands'] = [{'pc': '0x006EF550'}]
        entry = r['candidate_path_evidence']['candidates'][0]
        entry['accesses'][0]['direction'] = 'unknown'
        entry['static_read_occurrences'] = 0
        entry['unknown_direction_occurrences'] = 1
        r['overview']['candidate_offsets'][0]['static_read_occurrences'] = 0
        r['overview']['candidate_offsets'][0]['unknown_direction_occurrences'] = 1
        entry['static_read_and_write_shapes_both_present'] = False
        rows = p46.validate_bundle(r)
        rendered = p46.render_markdown(r, rows, False)
        self.assertIn('unknown-direction', rendered)
        self.assertIn('complex ESI', rendered)


class CLIAndAuthenticationTests(unittest.TestCase):
    def test_fake_report_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / 'bad.json', Path(d) / 'review.md'
            source.write_text('{not valid JSON', encoding='utf-8')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p46.main([str(source), '--output', str(out)])
            self.assertFalse(out.exists())

    def test_cli_review_without_exe_is_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / 'phase45.json', Path(d) / 'review.md'
            source.write_text(json.dumps(fixture()), encoding='utf-8')
            self.assertEqual(p46.main([str(source), '--output', str(out)]), 0)
            self.assertIn('NOT AUTHENTICATED', out.read_text())

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / 'phase45.json', Path(d) / 'review.md'
            source.write_text(json.dumps(fixture()), encoding='utf-8')
            out.write_text('original')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p46.main([str(source), '--output', str(out)])
            self.assertEqual(out.read_text(), 'original')

    def test_output_cannot_equal_json_input(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'report.json'
            original = json.dumps(fixture())
            source.write_text(original)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p46.main([str(source), '--output', str(source), '--overwrite'])
            self.assertEqual(source.read_text(), original)

    def test_symlink_output_to_input_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / 'phase45.json', Path(d) / 'review.md'
            original = json.dumps(fixture())
            source.write_text(original)
            out.symlink_to(source)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p46.main([str(source), '--output', str(out), '--overwrite'])
            self.assertEqual(source.read_text(), original)

    def test_report_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'report.json'
            source.write_bytes(b' ' * (p46.MAX_REPORT_BYTES + 1))
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p46.main([str(source)])

    def test_original_auth_mismatch_rejected(self):
        # Use a fake local module for isolated unit tests. No actual game binary.
        import types
        module = types.ModuleType('physics.phase45.carbon_pc_steering_evidence_bundle')
        module.audit_exact_source = lambda _: {'different': 'synthetic'}
        with patch.dict(sys.modules, {module.__name__: module}):
            with self.assertRaisesRegex(ValueError, 'differs'):
                p46.authenticate_with_executable(fixture(), b'fake')

    def test_original_auth_equal_synthetic_fixture(self):
        import types
        module = types.ModuleType('physics.phase45.carbon_pc_steering_evidence_bundle')
        module.audit_exact_source = lambda _: fixture()
        with patch.dict(sys.modules, {module.__name__: module}):
            p46.authenticate_with_executable(fixture(), b'synthetic')

    def test_cli_recomputed_failure_creates_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            source, exe, out = Path(d) / 'phase45.json', Path(d) / 'NFSC.exe', Path(d) / 'review.md'
            source.write_text(json.dumps(fixture()), encoding='utf-8')
            exe.write_bytes(b'synthetic')
            with patch.object(p46, 'authenticate_with_executable', side_effect=ValueError('bad source')):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    p46.main([str(source), '--exe', str(exe), '--output', str(out)])
            self.assertFalse(out.exists())

    def test_cli_auth_flag_requires_success(self):
        with tempfile.TemporaryDirectory() as d:
            source, exe, out = Path(d) / 'phase45.json', Path(d) / 'NFSC.exe', Path(d) / 'review.md'
            source.write_text(json.dumps(fixture()), encoding='utf-8')
            exe.write_bytes(b'synthetic')
            with patch.object(p46, 'authenticate_with_executable', return_value=None) as auth:
                self.assertEqual(p46.main([str(source), '--exe', str(exe), '--output', str(out)]), 0)
            auth.assert_called_once()
            self.assertIn('Recomputed from the local exact original', out.read_text())


if __name__ == '__main__':
    unittest.main()
