#!/usr/bin/env python3
"""Phase 46: validate and summarize Phase45 Carbon PC steering evidence.

A JSON report by itself is self-declared data, NEVER authenticated source proof.
With --exe, re-run Phase45's SHA-gated analysis and require exact equality.
No executables, assets, binary data, or runtime memory appear in Markdown.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUPPORTED_SHA256 = 'baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3'
EXPECTED = ((0x104, '0x006EF7B9', 'eax'), (0x118, '0x006EF7C0', 'edx'))
DIRECTIONS = frozenset(('read', 'write', 'read_write', 'unknown'))
READS = frozenset(('read', 'read_write'))
WRITES = frozenset(('write', 'read_write'))
STATES = frozenset(('no_detected_esi_write', 'esi_definition_seen', 'unknown_esi_effect'))
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_ACCESS_ROWS = 4096


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def obj(value: object, path: str) -> dict:
    require(isinstance(value, dict), f'{path} must be an object')
    return value


def array(value: object, path: str, maximum: int = MAX_ACCESS_ROWS) -> list:
    require(isinstance(value, list) and len(value) <= maximum,
            f'{path} must be a bounded list')
    return value


def nonnegative(value: object, path: str) -> int:
    require(type(value) is int and value >= 0, f'{path} must be a nonnegative integer')
    return value


def address(value: object, path: str) -> int:
    require(isinstance(value, str) and re.fullmatch(r'0x[0-9A-Fa-f]{8}', value) is not None,
            f'{path} must be a canonical 8-digit hexadecimal address')
    return int(value, 16)


def check_path(value: object, before: int, after: int, path: str) -> dict:
    evidence = obj(value, path)
    require(address(evidence.get('earlier_pc'), path + '.earlier_pc') == before,
            f'{path} earlier address mismatch')
    require(address(evidence.get('later_pc'), path + '.later_pc') == after,
            f'{path} later address mismatch')
    states = array(evidence.get('modeled_target_states'), path + '.modeled_target_states', 3)
    require(len(states) == len(set(states)) and set(states) <= STATES,
            f'{path} contains invalid or duplicate path states')
    require(evidence.get('modeled_routes_to_target') is bool(states),
            f'{path} reachability disagrees with states')
    for state, field in (
        ('no_detected_esi_write', 'route_with_no_detected_esi_write'),
        ('esi_definition_seen', 'route_with_esi_definition'),
        ('unknown_esi_effect', 'route_with_uncertain_esi_effect'),
    ):
        require(evidence.get(field) is (state in states), f'{path}.{field} disagrees')
    require(evidence.get('same_runtime_object_proven') is False,
            f'{path} improperly claims runtime object identity')
    require(evidence.get('real_execution_observed') is False,
            f'{path} improperly claims real execution')
    nonnegative(evidence.get('explored_static_states'), path + '.explored_static_states')
    issues = array(evidence.get('unresolved_or_exiting_controls_encountered'),
                   path + '.unresolved_or_exiting_controls_encountered', 64)
    require(all(isinstance(x, str) and re.fullmatch(r'[a-z_]+', x) for x in issues),
            f'{path} invalid control labels')
    return evidence


def validate_bundle(value: object) -> list[dict]:
    """Cross-check internal evidence. Does NOT verify NFSC.exe authenticity."""
    r = obj(value, 'report')
    require(r.get('phase') == 45 and r.get('schema_version') == 1,
            'only Phase45 schema version 1 is supported')
    source = obj(r.get('source'), 'source')
    require(source.get('platform') == 'Carbon PC', 'unexpected platform')
    require(source.get('sha256') == SUPPORTED_SHA256,
            'declared source SHA does not match supported Carbon PC build')
    require(source.get('steering_function_va') == '0x006EF540', 'unexpected function address')
    require(source.get('function_length_bytes') == 729, 'unexpected function length')
    require(nonnegative(source.get('verified_phase31_checks'), 'source.verified_phase31_checks') == 17,
            'unexpected Phase31 check count')
    verification = obj(r.get('verification'), 'verification')
    require(verification.get('phase31_sha_and_anchor_gate') == 'enforced_by_real_cli',
            'report lacks Phase45 gate declaration')
    for key in ('known_store_instruction_boundaries_checked',
                'complete_function_instruction_coverage_checked'):
        require(verification.get(key) is True, f'verification.{key} must be true')
    for key in ('source_binary_embedded_in_report',
                'ps2_to_pc_field_equivalence_verified',
                'runtime_gameplay_execution_observed',
                'steering_handling_patch_produced'):
        require(verification.get(key) is False, f'verification.{key} must be false')

    overview = obj(r.get('overview'), 'overview')
    nonnegative(overview.get('decoded_function_instructions'), 'overview.decoded_function_instructions')
    require(overview.get('known_store_anchor_count') == 2, 'unexpected store anchor count')
    census_total = nonnegative(overview.get('simple_esi_memory_access_count'), 'overview.simple_esi_memory_access_count')
    complex_count = nonnegative(overview.get('complex_esi_operand_count'), 'overview.complex_esi_operand_count')
    unparsed_count = nonnegative(overview.get('unparsed_memory_operand_form_count'), 'overview.unparsed_memory_operand_form_count')
    unresolved = obj(r.get('unresolved_address_forms'), 'unresolved_address_forms')
    require(len(array(unresolved.get('complex_esi_operands'), 'complex_esi_operands')) == complex_count,
            'complex ESI form count mismatch')
    require(len(array(unresolved.get('unparsed_memory_operand_forms'), 'unparsed_memory_operand_forms')) == unparsed_count,
            'unparsed memory form count mismatch')

    summaries = array(overview.get('candidate_offsets'), 'overview.candidate_offsets', 2)
    candidates = array(obj(r.get('candidate_path_evidence'), 'candidate_path_evidence').get('candidates'),
                       'candidate_path_evidence.candidates', 2)
    register_traces = array(r.get('register_origin_evidence'), 'register_origin_evidence', 2)
    require(len(summaries) == len(candidates) == len(register_traces) == 2,
            'expected exactly two candidate fields and two register traces')
    path_evidence = obj(r['candidate_path_evidence'], 'candidate_path_evidence')
    check_path(path_evidence.get('anchor_to_anchor'), 0x006EF7B9, 0x006EF7C0,
               'anchor_to_anchor')
    issue_counts = obj(path_evidence.get('cfg_issue_counts'), 'cfg_issue_counts')
    require(all(isinstance(k, str) and re.fullmatch(r'[a-z_]+', k) and type(v) is int and v >= 0
                for k, v in issue_counts.items()), 'invalid CFG issue count')
    findings = []
    covered_accesses = 0
    for i, (offset, pc, register) in enumerate(EXPECTED):
        summary = obj(summaries[i], f'summary[{i}]')
        detail = obj(candidates[i], f'candidate[{i}]')
        trace = obj(register_traces[i], f'register_trace[{i}]')
        require(summary.get('candidate_offset') == detail.get('signed_displacement') == offset,
                f'candidate {i} offset mismatch')
        require(summary.get('known_store_pc') == detail.get('known_store_pc') == pc,
                f'candidate {i} anchor PC mismatch')
        require(summary.get('classification') == 'syntactic_esi_relative_memory_operand' and
                summary.get('semantic_role') == 'unverified' and
                summary.get('matching_ps2_offset') is None,
                f'candidate {i} incorrectly asserts semantic field identity')
        require(trace.get('instruction_pc') == pc and trace.get('source_register') == register,
                f'register trace {i} PC/register mismatch')
        require(trace.get('field_semantics') == 'unknown', f'register trace {i} claims field semantics')
        require(trace.get('syntactic_destination') == f'[esi+0x{offset:x}]',
                f'register trace {i} destination mismatch')
        origin = obj(trace.get('source_register_local_trace'), f'register trace {i} origin')
        require(isinstance(origin.get('status'), str) and
                re.fullmatch(r'[a-z_]+', origin['status']), f'invalid register trace {i} status')
        access = array(detail.get('accesses'), f'candidate[{i}].accesses')
        require(access, f'candidate {i} must contain anchor')
        pcs = [address(obj(item, 'access').get('pc'), 'access.pc') for item in access]
        require(pcs == sorted(set(pcs)), f'candidate {i} access PCs duplicated/unordered')
        directions = [item.get('direction') for item in access]
        require(set(directions) <= DIRECTIONS, f'candidate {i} invalid direction')
        require(sum(d in READS for d in directions) == summary.get('static_read_occurrences') == detail.get('static_read_occurrences'),
                f'candidate {i} static read count mismatch')
        require(sum(d in WRITES for d in directions) == summary.get('static_write_occurrences') == detail.get('static_write_occurrences'),
                f'candidate {i} static write count mismatch')
        require(directions.count('unknown') == summary.get('unknown_direction_occurrences') == detail.get('unknown_direction_occurrences'),
                f'candidate {i} unknown direction count mismatch')
        require(summary.get('candidate_access_pcs') == [a['pc'] for a in access],
                f'candidate {i} access PCs differ')
        require(sum(item['pc'] == pc and item['direction'] == 'write'
                    and item.get('known_phase40_anchor') is True for item in access) == 1,
                f'candidate {i} lacks exact known store anchor')
        require(detail.get('static_read_and_write_shapes_both_present') is
                (any(d in READS for d in directions) and any(d in WRITES for d in directions)),
                f'candidate {i} read/write shape flag mismatch')
        spans = array(detail.get('consecutive_same_offset_spans'), f'candidate[{i}].spans')
        require(len(spans) == len(access) - 1 == summary.get('modeled_inter_access_paths'),
                f'candidate {i} inter-access span count mismatch')
        concern_counts = {'unknown_paths': 0, 'definition_paths': 0, 'unreachable_spans': 0}
        for j, span in enumerate(spans):
            s = obj(span, f'candidate[{i}].span[{j}]')
            require(address(s.get('earlier_pc'), 'span.earlier_pc') == pcs[j] and
                    address(s.get('later_pc'), 'span.later_pc') == pcs[j + 1],
                    f'candidate {i} span order mismatch')
            path = check_path(s.get('cfg_path_evidence'), pcs[j], pcs[j + 1],
                              f'candidate[{i}].span[{j}].cfg')
            concern_counts['unknown_paths'] += int(path['route_with_uncertain_esi_effect'])
            concern_counts['definition_paths'] += int(path['route_with_esi_definition'])
            concern_counts['unreachable_spans'] += int(not path['modeled_routes_to_target'])
        covered_accesses += len(access)
        findings.append({
            'offset': offset, 'store_pc': pc, 'register': register,
            'reads': summary['static_read_occurrences'],
            'writes': summary['static_write_occurrences'],
            'unknown_directions': summary['unknown_direction_occurrences'],
            'register_trace_status': origin['status'],
            'access_count': len(access), **concern_counts,
        })
    require(covered_accesses <= census_total,
            'candidate access total exceeds full ESI census')
    return findings


def authenticate_with_executable(report: dict, exe_data: bytes) -> None:
    """Recompute full Phase45 report from the exact executable and compare it.

    No equality fallback for missing tools or source; a mismatched report fails.
    """
    from physics.phase45.carbon_pc_steering_evidence_bundle import audit_exact_source
    recomputed = audit_exact_source(exe_data)
    require(recomputed == report, 'report differs from freshly verified original executable analysis')


def render_markdown(report: dict, findings: list[dict], authenticated: bool) -> str:
    sha = report['source']['sha256']
    state = ('Recomputed from the local exact original executable and matched the report.'
             if authenticated else
             'NOT AUTHENTICATED: JSON metadata is self-declared. No original executable was checked.')
    lines = [
        '# Phase 46: Carbon PC steering evidence review', '',
        f'**Source-authentication status:** {state}', '',
        f'**Declared executable SHA-256:** `{sha}`', '',
        'This is a static instruction and control-flow review, **not** proof of steering-field names, PC/PS2 object equivalence, or in-game behavior.', '',
        '## Candidate steering-state accesses', '',
        '| ESI displacement | Anchored store PC | Source register | Static reads | Static writes | Unknown directions | Local register origin |',
        '| --- | --- | --- | ---: | ---: | ---: | --- |',
    ]
    for row in findings:
        lines.append(f"| `+0x{row['offset']:X}` | `{row['store_pc']}` | `{row['register']}` | {row['reads']} | {row['writes']} | {row['unknown_directions']} | `{row['register_trace_status']}` |")
    lines += ['', '## Follow-up checks', '']
    for item in findings:
        key = f"`+0x{item['offset']:X}` ({item['store_pc']})"
        if item['register_trace_status'] != 'known_zero':
            lines.append(f"- {key}: inspect `{item['register']}` provenance (`{item['register_trace_status']}`); a local trace is not field semantics.")
        if item['unknown_directions']:
            lines.append(f"- {key}: classify {item['unknown_directions']} unknown-direction instruction(s) using source-backed decoding.")
        if item['unknown_paths'] or item['definition_paths'] or item['unreachable_spans']:
            lines.append(f"- {key}: review {item['unknown_paths']} uncertain-path, {item['definition_paths']} ESI-definition-path, and {item['unreachable_spans']} unreachable modeled span(s).")
        if not item['reads']:
            lines.append(f"- {key}: no direct reads were listed for this exact offset; search indirect and complex addressing before inferring write-only behavior.")
    unresolved = report['overview']
    if unresolved['complex_esi_operand_count'] or unresolved['unparsed_memory_operand_form_count']:
        lines.append(f"- Review {unresolved['complex_esi_operand_count']} complex ESI addressing forms and {unresolved['unparsed_memory_operand_form_count']} unparsed memory forms that might hide other accesses.")
    lines += [
        '- Validate the actual object identity, data type, and unit before comparing against Undercover PS2 steering.',
        '- Any experimental steering hook must be opt-in, reversible, and guarded by the exact Carbon PC build.', '',
        '## Boundaries', '',
        '- The original Carbon executable and its instruction bytes are never included in this review.',
        '- A clean modeled CFG path does not establish that the path executes while driving.',
        '- PS2 +0x188/+0x19C are not verified equivalents of Carbon PC +0x104/+0x118.',
        '- Phase 30 lateral tire-force modification stays disabled.', '',
    ]
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path, help='Existing Phase45 JSON file')
    parser.add_argument('--exe', type=Path, help='Optional exact original NFSC.exe, to recompute and authenticate report')
    parser.add_argument('--output', type=Path, help='Markdown report; stdout by default')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        require(args.report.stat().st_size <= MAX_REPORT_BYTES, 'report exceeds 8 MiB limit')
        report = json.loads(args.report.read_text(encoding='utf-8'))
        findings = validate_bundle(report)
        if args.exe:
            authenticate_with_executable(report, args.exe.read_bytes())
        markdown = render_markdown(report, findings, bool(args.exe))
        if args.output:
            require(args.output.suffix.lower() in ('.md', '.markdown'),
                    'output must use a Markdown extension, never an executable extension')
            targets = [args.report] + ([args.exe] if args.exe else [])
            require(all(args.output.resolve() != target.resolve() for target in targets),
                    'output path must not equal report or source executable')
            with args.output.open('w' if args.overwrite else 'x', encoding='utf-8') as f:
                f.write(markdown)
            print('Phase 46 review saved:', args.output)
        else:
            print(markdown, end='')
        return 0
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(1, f'FAIL (no game changes): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
