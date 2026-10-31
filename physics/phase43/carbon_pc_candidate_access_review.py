#!/usr/bin/env python3
"""Phase 43: syntactic Carbon PC +0x104/+0x118 access review.

Combines Phase42's SHA-gated memory census with Phase41's conservative
instruction-boundary/ESI-write barriers. Neither offsets nor instruction
order are proof of a particular object, steering field, or runtime path.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physics.phase40.carbon_pc_store_audit import (  # noqa: E402
    ANCHOR_ADDRESSES, STEERING_START, STEERING_END, at, save_report, sections,
)
from physics.phase41.carbon_pc_register_trace import (  # noqa: E402
    boundaries, describe_effect, disassemble,
)
from physics.phase42.carbon_pc_esi_access_census import (  # noqa: E402
    audit_verified_pc, find_accesses,
)

CANDIDATE_OFFSETS = (0x104, 0x118)
DIRECT_READ = frozenset(('read', 'read_write'))
DIRECT_WRITE = frozenset(('write', 'read_write'))
NEARBY_BYTES = 48


def validate_instructions(instructions: list[dict]) -> dict[int, dict]:
    """Reject duplicate, unordered, noncontiguous instruction records."""
    if not instructions:
        raise ValueError('empty decoded steering instruction sequence')
    index = {}
    end = None
    for ins in instructions:
        pc, size = ins['pc'], ins['length']
        if not isinstance(pc, int) or not isinstance(size, int) or size < 1 or size > 15:
            raise ValueError('invalid decoded instruction bounds')
        if pc in index or (end is not None and pc != end):
            raise ValueError('duplicate, overlapping or noncontiguous x86 instructions')
        index[pc] = ins
        end = pc + size
    return index


def span_evidence(instructions: list[dict], begin: int, end: int) -> dict:
    """Check a lexical instruction span for control or uncertain ESI writes.

    Passing this check does NOT establish that both accesses execute on a
    single path or share the same source-level object across function calls.
    """
    index = validate_instructions(instructions)
    if begin not in index or end not in index or begin >= end:
        raise ValueError('span endpoints must be ordered instruction addresses')
    starts = boundaries(instructions)
    if any(begin < block_start <= end for block_start in starts):
        return {
            'status': 'control_flow_boundary',
            'evidence_pc': [f'0x{p:08X}' for p in sorted(starts) if begin < p <= end],
            'same_runtime_object_proven': False,
        }
    for ins in instructions:
        if not begin <= ins['pc'] < end:
            continue  # First memory access can itself redefine ESI (e.g. MOV ESI,[ESI+off]).
        effect = describe_effect(ins, 'esi')
        kind = effect['kind']
        if kind == 'opaque_barrier':
            return {'status': 'unknown_instruction_effect',
                    'evidence_pc': [f"0x{ins['pc']:08X}"],
                    'same_runtime_object_proven': False}
        if kind.startswith('skip_'):
            continue
        return {'status': 'esi_definition_or_implicit_effect',
                'effect': kind, 'evidence_pc': [f"0x{ins['pc']:08X}"],
                'same_runtime_object_proven': False}
    return {
        'status': 'no_detected_esi_write_in_same_linear_region',
        'evidence_pc': [],
        'same_runtime_object_proven': False,
    }


def build_review(instructions: list[dict], census: dict,
                 anchors: tuple[int, int] = ANCHOR_ADDRESSES) -> dict:
    """Build a local static review from an authenticated census or fixture.

    The public CLI only calls this after Phase42's exact-executable verifier.
    """
    instruction_index = validate_instructions(instructions)
    rows = census.get('simple_esi_accesses')
    if not isinstance(rows, list):
        raise ValueError('missing Phase 42 access evidence')
    regenerated = find_accesses(instructions)['simple_esi_accesses']
    if rows != regenerated:
        raise ValueError('Phase 42 evidence and decoded instructions disagree')
    if len(anchors) != 2:
        raise ValueError('exactly two known store anchors required')
    expected = dict(zip(anchors, CANDIDATE_OFFSETS))
    for pc, offset in expected.items():
        hits = [r for r in rows if int(r['pc'], 16) == pc and
                r['signed_displacement'] == offset and
                r['direction'] == 'write' and
                r['base_register'] == 'esi']
        if len(hits) != 1 or pc not in instruction_index:
            raise ValueError(f'verified store anchor missing at {pc:#x}')
    result = []
    for offset in CANDIDATE_OFFSETS:
        selected = [r for r in rows if r['signed_displacement'] == offset]
        seen = [int(r['pc'], 16) for r in selected]
        if seen != sorted(set(seen)):
            raise ValueError('duplicate or unsorted candidate access PC')
        directions = Counter(r['direction'] for r in selected)
        neighbors = []
        for target in selected:
            tpc = int(target['pc'], 16)
            near = [
                {'pc': other['pc'],
                 'signed_displacement': other['signed_displacement'],
                 'direction': other['direction'],
                 'distance_bytes': int(other['pc'], 16) - tpc}
                for other in rows
                if other['pc'] != target['pc'] and
                abs(int(other['pc'], 16) - tpc) <= NEARBY_BYTES
            ]
            neighbors.append({'candidate_pc': target['pc'],
                              'nearby_explicit_esi_operands': near})
        consecutive = [
            {
                'earlier_pc': selected[i]['pc'],
                'later_pc': selected[i + 1]['pc'],
                'earlier_direction': selected[i]['direction'],
                'later_direction': selected[i + 1]['direction'],
                'static_span': span_evidence(instructions, seen[i], seen[i + 1]),
            }
            for i in range(len(selected) - 1)
        ]
        result.append({
            'signed_displacement': offset,
            'known_store_pc': f"0x{next(pc for pc, x in expected.items() if x == offset):08X}",
            'static_read_occurrences': sum(directions[direction] for direction in DIRECT_READ),
            'static_write_occurrences': sum(directions[direction] for direction in DIRECT_WRITE),
            'unknown_direction_occurrences': directions['unknown'],
            'accesses': [{
                'pc': r['pc'], 'mnemonic': r['mnemonic'],
                'direction': r['direction'],
                'known_phase40_anchor': r['known_phase40_anchor'],
            } for r in selected],
            'consecutive_same_offset_spans': consecutive,
            'nearby_esi_access_context': neighbors,
            'static_read_and_write_shapes_both_present':
                any(r['direction'] in DIRECT_READ for r in selected) and
                any(r['direction'] in DIRECT_WRITE for r in selected),
        })
    return {
        'phase': 43,
        'scope': 'static syntactic PC access review, not runtime state dependency',
        'source_sha256': census.get('source_sha256'),
        'candidate_offsets': result,
        'known_anchor_linear_span': span_evidence(instructions, *anchors),
        'phase42_simple_esi_access_count': census.get('simple_esi_access_count'),
        'phase42_complex_esi_operand_count': census.get('complex_esi_operand_count'),
        'field_names_verified': False,
        'ps2_pc_field_equivalence_verified': False,
        'runtime_path_or_object_identity_verified': False,
        'gameplay_patch_created': False,
        'limitations': [
            'A static read and write of one offset need not run on the same branch.',
            'ESI may be different across control-flow paths or function calls.',
            'Only simple explicit ESI-relative memory operands are counted.',
            'A clean local span is not source-level object-identity evidence.',
            'Indexed and indirect accesses may be absent from candidate lists.',
            'No PS2 offset equivalence or steering-behavior changes are proven.',
        ],
    }


def audit_verified_image(data: bytes) -> dict:
    """Phase42 must validate the complete original executable before analysis."""
    verified_census = audit_verified_pc(data)
    raw = at(data, sections(data), STEERING_START, STEERING_END - STEERING_START)
    instructions = disassemble(raw, STEERING_START)
    return build_review(instructions, verified_census)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='Exact supported, user-owned Carbon PC NFSC.exe')
    parser.add_argument('--output', type=Path, help='Output JSON (stdout by default)')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = audit_verified_image(args.exe.read_bytes())
        output = json.dumps(result, indent=2) + '\n'
        if args.output:
            save_report(args.output, output, args.overwrite, args.exe)
            print('Phase 43 review report:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError, RuntimeError, TypeError, KeyError) as exc:
        parser.exit(1, f'FAIL (game remains unchanged): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
