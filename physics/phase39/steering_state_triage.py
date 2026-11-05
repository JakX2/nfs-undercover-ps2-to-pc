#!/usr/bin/env python3
"""Phase 39: build a review queue from SHA-gated Phase 38 steering access traces.

Structural differences are *leads*, not proven semantics, runtime behavior or
Carbon PC offsets. The CLI reads only exact verified original PS2 binaries.
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
from physics.phase38.register_provenance import audit_source_file  # noqa: E402

EXPECTED_BUILDS = ('undercover_ps2', 'carbon_ps2')
ANCHOR_LABELS = ('chassis_input', 'chassis_input',
                 'racer_shaped_input_write', 'racer_steering_write')
REGIONS = ('before_input_1', 'input_1_to_input_2',
           'input_2_to_shaped_output', 'shaped_output_to_steering_output',
           'after_steering_output')
TERMINAL_UNCERTAIN = frozenset(('block_live_in_unknown', 'opaque_barrier',
                                'unknown_definition', 'depth_limit',
                                'partial_load_unknown'))
SUPPORTED_PROVENANCE = TERMINAL_UNCERTAIN | frozenset((
    'architectural_zero', 'lui', 'addiu', 'ori', 'move', 'binary', 'load'))


def provenance_signature(node: dict, depth: int = 0) -> tuple:
    """Machine-independent instruction-shape sketch, not pointer equivalence."""
    if depth > 32 or not isinstance(node, dict):
        raise ValueError('invalid or oversized provenance tree')
    kind = node.get('kind')
    if kind not in SUPPORTED_PROVENANCE:
        raise ValueError(f'unsupported provenance node: {kind!r}')
    if kind in TERMINAL_UNCERTAIN:
        return (kind,)
    if kind == 'architectural_zero':
        return (kind,)
    if kind == 'lui':
        return (kind,)  # ignore relocatable immediate and PC
    if kind == 'load':
        offset = node.get('displacement')
        if not isinstance(offset, int):
            raise ValueError('missing load displacement')
        return (kind, offset, provenance_signature(node.get('address_base'), depth + 1))
    if kind in ('addiu', 'ori', 'move'):
        return (kind, provenance_signature(node.get('source'), depth + 1))
    if kind == 'binary':
        sources = node.get('sources')
        if not isinstance(sources, list) or len(sources) != 2:
            raise ValueError('binary provenance must have two source nodes')
        return (kind, *(provenance_signature(n, depth + 1) for n in sources))
    raise ValueError('invalid provenance')


def unresolved_leaves(node: dict, depth: int = 0) -> list[str]:
    if depth > 32 or not isinstance(node, dict):
        raise ValueError('invalid or oversized provenance tree')
    kind = node.get('kind')
    if kind not in SUPPORTED_PROVENANCE:
        raise ValueError('unknown provenance kind')
    if kind in TERMINAL_UNCERTAIN:
        return [kind]
    if kind in ('architectural_zero', 'lui'):
        return []
    if kind == 'load':
        return unresolved_leaves(node.get('address_base'), depth + 1)
    if kind in ('addiu', 'ori', 'move'):
        return unresolved_leaves(node.get('source'), depth + 1)
    if kind == 'binary':
        srcs = node.get('sources')
        if not isinstance(srcs, list) or len(srcs) != 2:
            raise ValueError('invalid binary provenance')
        return (unresolved_leaves(srcs[0], depth + 1)
                + unresolved_leaves(srcs[1], depth + 1))
    raise ValueError('invalid provenance')


def shape(row: dict) -> tuple:
    return row['mnemonic'], row['signed_displacement'], row['direction']


def label_regions(report: dict) -> dict[str, list[dict]]:
    """Partition in instruction order without equating either game's objects."""
    rows = report.get('candidate_accesses')
    if not isinstance(rows, list):
        raise ValueError('missing Phase 38 candidate accesses')
    if not all(isinstance(r, dict) for r in rows):
        raise ValueError('invalid access record')
    pcs = [int(r['pc'], 16) for r in rows]
    if pcs != sorted(set(pcs)):
        raise ValueError('candidate accesses must be strictly ordered and unique')
    anchors = [r for r in rows if r.get('evidence_label')]
    if tuple(r['evidence_label'] for r in anchors) != ANCHOR_LABELS:
        raise ValueError('missing or reordered Phase 33 steering anchors')
    if tuple((r['signed_displacement'], r['direction']) for r in anchors) != (
        (0x8c, 'read'), (0x8c, 'read'), (0x19c, 'write'), (0x188, 'write')
    ):
        raise ValueError('unexpected anchor displacement or direction')
    anchors_pc = [int(r['pc'], 16) for r in anchors]
    output = {r: [] for r in REGIONS}
    for row in rows:
        provenance_signature(row['base_provenance'])
        if row.get('evidence_label'):
            continue
        pc = int(row['pc'], 16)
        region = sum(pc > a for a in anchors_pc)
        output[REGIONS[region]].append(row)
    return output


def compare_reports(uc: dict, carbon: dict) -> dict:
    """Evidence triage for original-binary reports or synthetic test reports.

    DOES NOT validate any ELF input itself; the public CLI always calls
    Phase38 audit_source_file, which performs exact Phase33/36 verification.
    """
    if (uc.get('build'), carbon.get('build')) != EXPECTED_BUILDS:
        raise ValueError('expected Undercover PS2 and Carbon PS2 in that order')
    u_regions = label_regions(uc)
    c_regions = label_regions(carbon)
    reviews = []
    region_summaries = []
    for name in REGIONS:
        a, b = u_regions[name], c_regions[name]
        ua, cb = Counter(map(shape, a)), Counter(map(shape, b))
        region_summaries.append({
            'region': name, 'undercover_candidate_accesses': len(a),
            'carbon_candidate_accesses': len(b),
            'undercover_unresolved_bases': sum(bool(unresolved_leaves(r['base_provenance'])) for r in a),
            'carbon_unresolved_bases': sum(bool(unresolved_leaves(r['base_provenance'])) for r in b),
        })
        for token in sorted(set(ua) | set(cb)):
            left = [r for r in a if shape(r) == token]
            right = [r for r in b if shape(r) == token]
            signatures_left = [provenance_signature(r['base_provenance']) for r in left]
            signatures_right = [provenance_signature(r['base_provenance']) for r in right]
            classification = None
            if len(left) != len(right):
                classification = 'instruction_shape_count_difference'
            elif Counter(signatures_left) != Counter(signatures_right):
                classification = 'local_provenance_shape_difference'
            if classification is None:
                continue
            reviews.append({
                'region': name, 'classification': classification,
                'mnemonic': token[0], 'signed_displacement': token[1],
                'direction': token[2],
                'undercover_count': len(left), 'carbon_count': len(right),
                'undercover_pc': [r['pc'] for r in left],
                'carbon_pc': [r['pc'] for r in right],
                'undercover_unresolved_roots': sorted(set(
                    kind for r in left for kind in unresolved_leaves(r['base_provenance']))),
                'carbon_unresolved_roots': sorted(set(
                    kind for r in right for kind in unresolved_leaves(r['base_provenance']))),
                'repeated_pattern_ambiguity': max(len(left), len(right)) > 1,
            })
    reviews.sort(key=lambda r: (REGIONS.index(r['region']),
                                0 if r['classification'] == 'instruction_shape_count_difference' else 1,
                                r['signed_displacement'], r['mnemonic'], r['direction']))
    return {
        'phase': 39, 'schema_version': 1,
        'source_sha256': {'undercover_ps2': uc.get('sha256'),
                          'carbon_ps2': carbon.get('sha256')},
        'purpose': 'Manual review queue for static, source-verified PS2 steering access shapes',
        'scope_warning': ('A difference in an instruction or local provenance shape is NOT '
                          'a proven steering-behavior difference, a shared field identity, '
                          'or a Carbon PC mapping.'),
        'regions': region_summaries,
        'manual_review_queue': reviews,
        'candidate_review_count': len(reviews),
        'next_evidence_required': [
            'Run exact original PS2 executables through the SHA-gated auditor.',
            'Manually inspect register and control-flow origins for candidate PCs.',
            'Independently confirm state-field types and Carbon PC equivalents.',
            'Perform opt-in read-only PC observations before an actual steering patch.',
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uc', type=Path, required=True, help='Original Undercover PS2 ELF')
    parser.add_argument('--carbon', type=Path, required=True, help='Original Carbon PS2 ELF')
    parser.add_argument('--output', type=Path, help='JSON report (stdout otherwise)')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        # Both SHA checks and original-binary structural verification are performed
        # upstream, before examining provenance or writing any output.
        reports = [audit_source_file(args.uc.read_bytes(), 'undercover_ps2'),
                   audit_source_file(args.carbon.read_bytes(), 'carbon_ps2')]
        result = compare_reports(*reports)
        output = json.dumps(result, indent=2) + '\n'
        if args.output:
            with args.output.open('w' if args.overwrite else 'x', encoding='utf8') as f:
                f.write(output)
            print('Phase 39 saved:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.exit(1, f'FAIL (no game changes): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
