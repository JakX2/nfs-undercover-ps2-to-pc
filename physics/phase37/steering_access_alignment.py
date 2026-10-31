#!/usr/bin/env python3
"""Phase 37: anchor-partitioned static steering-access sequence comparison.

Original binaries are verified by Phase 33 through Phase 36 before scanning.
A shared opcode/displacement shape is not an object identity or PC mapping.
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
from physics.phase36.steering_memory_audit import audit_original  # noqa: E402

EXPECTED_ANCHORS = (
    'chassis_input', 'chassis_input',
    'racer_shaped_input_write', 'racer_steering_write',
)


def fingerprint(row: dict) -> tuple[str, int]:
    """Strict instruction-shape token, never a semantic field label."""
    return row['mnemonic'], row['signed_displacement']


def anchor_indices(report: dict) -> list[int]:
    rows = report['accesses']
    indices = [i for i, row in enumerate(rows) if row['evidence_label']]
    if tuple(rows[i]['evidence_label'] for i in indices) != EXPECTED_ANCHORS:
        raise ValueError(f"missing or misordered verified anchors in {report['build']}")
    for i in indices:
        if rows[i]['candidate_offset'] == '':
            raise ValueError('verified anchor missing known candidate displacement')
    return indices


def lcs_pairs(left: list[dict], right: list[dict]) -> list[tuple[int, int]]:
    """Deterministic longest common subsequence of exact instruction shapes.

    Index pairs refer to input slices. A pair only has shape similarity.
    """
    n, m = len(left), len(right)
    if n > 1024 or m > 1024:
        raise ValueError('unexpectedly large access sequence')
    a, b = [fingerprint(x) for x in left], [fingerprint(x) for x in right]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            dp[i][j] = (dp[i + 1][j + 1] + 1 if a[i] == b[j]
                        else max(dp[i + 1][j], dp[i][j + 1]))
    i = j = 0
    pairs = []
    while i < n and j < m:
        if a[i] == b[j] and dp[i][j] == dp[i + 1][j + 1] + 1:
            pairs.append((i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1  # consistent tie-break for ambiguous repeated fingerprints
        else:
            j += 1
    return pairs


def _compact(row: dict) -> dict:
    """No machine-code bytes, values, or raw executable content exported."""
    return {
        'pc': row['pc'], 'relative_pc': row['relative_pc'],
        'mnemonic': row['mnemonic'],
        'signed_displacement': row['signed_displacement'],
        'base_register': row['base_register'],
        'evidence_label': row['evidence_label'],
    }


def _segment(left: list[dict], right: list[dict], name: str) -> dict:
    matches = lcs_pairs(left, right)
    seen_left, seen_right = {i for i, _ in matches}, {j for _, j in matches}
    lc = Counter(map(fingerprint, left))
    rc = Counter(map(fingerprint, right))
    aligned = []
    for i, j in matches:
        token = fingerprint(left[i])
        aligned.append({
            'undercover': _compact(left[i]), 'carbon': _compact(right[j]),
            'repeated_shape': lc[token] > 1 or rc[token] > 1,
        })
    return {
        'region': name,
        'undercover_access_count': len(left),
        'carbon_access_count': len(right),
        'exact_shape_matches': len(matches),
        'repeated_shape_matches': sum(p['repeated_shape'] for p in aligned),
        'paired_static_shapes': aligned,
        'unpaired_undercover': [_compact(r) for i, r in enumerate(left) if i not in seen_left],
        'unpaired_carbon': [_compact(r) for j, r in enumerate(right) if j not in seen_right],
    }


def compare(undercover: dict, carbon: dict) -> dict:
    if (undercover.get('build'), carbon.get('build')) != ('undercover_ps2', 'carbon_ps2'):
        raise ValueError('requires Undercover PS2 then Carbon PS2 verified audits')
    ua, ca = undercover['accesses'], carbon['accesses']
    ui, ci = anchor_indices(undercover), anchor_indices(carbon)
    anchors = []
    for i, j in zip(ui, ci):
        u, c = ua[i], ca[j]
        if fingerprint(u) != fingerprint(c) or u['direction'] != c['direction']:
            raise ValueError('verified anchor changed instruction shape or direction')
        anchors.append({'label': u['evidence_label'],
                        'undercover': _compact(u), 'carbon': _compact(c)})
    intervals = []
    previous_u = previous_c = -1
    for k in range(len(ui) + 1):
        next_u, next_c = ((ui[k], ci[k]) if k < len(ui)
                          else (len(ua), len(ca)))
        intervals.append(_segment(ua[previous_u + 1:next_u],
                                  ca[previous_c + 1:next_c],
                                  f'between_anchor_{k}'))
        previous_u, previous_c = next_u, next_c
    return {
        'schema_version': 1,
        'study': 'phase37_anchor_partitioned_ps2_static_access_sequence',
        'original_file_sha256': {
            'undercover_ps2': undercover['source_sha256'],
            'carbon_ps2': carbon['source_sha256'],
        },
        'limitations': [
            'Static memory instructions only; no control-flow or branch-frequency analysis.',
            'Exact opcode/displacement matches do not prove field or object identity.',
            'Register numbers and pointer provenance are not aligned.',
            'Repeated fingerprints can admit multiple equally scoring alignments.',
            'Nothing here establishes Carbon PC offsets or actual steering feel.',
        ],
        'known_anchor_pairs': anchors,
        'regions': intervals,
        'total_static_shape_pairs': sum(x['exact_shape_matches'] for x in intervals) + len(anchors),
        'unpaired_undercover': sum(len(x['unpaired_undercover']) for x in intervals),
        'unpaired_carbon': sum(len(x['unpaired_carbon']) for x in intervals),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--uc', required=True, type=Path, help='Original Undercover PS2 ELF')
    p.add_argument('--carbon', required=True, type=Path, help='Original Carbon PS2 ELF')
    p.add_argument('--output', type=Path, help='JSON report (default: standard output)')
    p.add_argument('--overwrite', action='store_true')
    args = p.parse_args(argv)
    try:
        # audit_original performs Phase33 SHA + instruction + call-site validation.
        uc = audit_original(args.uc.read_bytes(), 'undercover_ps2')
        carbon = audit_original(args.carbon.read_bytes(), 'carbon_ps2')
        report = compare(uc, carbon)
        output = json.dumps(report, indent=2) + '\n'
        if args.output:
            with args.output.open('w' if args.overwrite else 'x', encoding='utf8') as f:
                f.write(output)
            print('Phase 37 report written:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError) as exc:
        p.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
