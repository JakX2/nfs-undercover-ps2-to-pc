#!/usr/bin/env python3
"""Phase 45: one-command, exact-build Carbon PC steering evidence bundle.

The CLI SHA-verifies the user-owned original via Phase 31/40 BEFORE bounded
disassembly. Public fixtures are synthetic. No game hooks or modifications.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physics.phase40.carbon_pc_store_audit import (  # noqa: E402
    ANCHOR_ADDRESSES, BYTES, STEERING_END, STEERING_START,
    at, decode_mov_store, extract_from_verified_image, save_report, sections,
)
from physics.phase41.carbon_pc_register_trace import (  # noqa: E402
    disassemble, trace_before,
)
from physics.phase42.carbon_pc_esi_access_census import find_accesses  # noqa: E402
from physics.phase43.carbon_pc_candidate_access_review import (  # noqa: E402
    build_review, validate_instructions,
)
from physics.phase44.carbon_pc_esi_cfg_audit import augment_review  # noqa: E402

SCHEMA_VERSION = 1
SCOPED_OFFSETS = (0x104, 0x118)
EXPECTED_SOURCE_REGISTERS = ('eax', 'edx')


def verify_anchor_disassembly(instructions: list[dict], verified: dict) -> list[dict]:
    """Assert both independently decoded instructions match Phase40 evidence.

    This compares instruction bytes and semantic operands, not only string
    labels from objdump. Nothing here authenticates arbitrary input by itself.
    """
    instruction_index = validate_instructions(instructions)
    source_stores = verified.get('known_steering_store_instructions')
    if not isinstance(source_stores, list) or len(source_stores) != 2:
        raise ValueError('Phase40 must provide exactly two verified store anchors')
    matched = []
    for address, offset, register, store in zip(
        ANCHOR_ADDRESSES, SCOPED_OFFSETS, EXPECTED_SOURCE_REGISTERS, source_stores
    ):
        ins = instruction_index.get(address)
        if ins is None:
            raise ValueError(f'missing independently decoded anchor at {address:#x}')
        raw = bytes.fromhex(BYTES[address])
        if ins['bytes'] != raw or ins['length'] != len(raw):
            raise ValueError(f'wrong instruction bytes or boundary at {address:#x}')
        decoded = decode_mov_store(raw, address)
        for key in ('address', 'base_register', 'source_register',
                    'signed_displacement', 'direction'):
            if store.get(key) != decoded[key]:
                raise ValueError(f'Phase40 metadata mismatch for {key} at {address:#x}')
        if (decoded['source_register'], decoded['signed_displacement'],
                decoded['base_register']) != (register, offset, 'esi'):
            raise ValueError(f'unexpected steering store identity at {address:#x}')
        matched.append(decoded)
    return matched


def review_from_decoded(instructions: list[dict], phase40: dict) -> dict:
    """Pure synthetic-testable composition. NOT an authentication entrypoint."""
    anchors = verify_anchor_disassembly(instructions, phase40)
    census = find_accesses(instructions)
    for anchor, displacement in zip(ANCHOR_ADDRESSES, SCOPED_OFFSETS):
        rows = [
            r for r in census['simple_esi_accesses']
            if int(r['pc'], 16) == anchor
            and r['signed_displacement'] == displacement
            and r['direction'] == 'write'
            and r['base_register'] == 'esi'
        ]
        if len(rows) != 1:
            raise ValueError(f'anchor not uniquely recovered in ESI access census: {anchor:#x}')

    trusted_census = {
        'source_sha256': phase40['exe_sha256'],
        'simple_esi_accesses': census['simple_esi_accesses'],
        'simple_esi_access_count': census['simple_esi_access_count'],
        'complex_esi_operand_count': census['complex_esi_operand_count'],
    }
    phase43 = build_review(instructions, trusted_census)
    phase44 = augment_review(instructions, phase43)
    stores = []
    for anchor in anchors:
        pc = int(anchor['address'], 16)
        stores.append({
            'instruction_pc': anchor['address'],
            'syntactic_destination': anchor['syntactic_destination'],
            'source_register': anchor['source_register'],
            'source_register_local_trace': trace_before(
                instructions, pc, anchor['source_register']
            ),
            'field_semantics': 'unknown',
        })

    overview = []
    for field in phase44['candidate_offsets']:
        offset = field['signed_displacement']
        overview.append({
            'candidate_offset': offset,
            'classification': 'syntactic_esi_relative_memory_operand',
            'static_read_occurrences': field['static_read_occurrences'],
            'static_write_occurrences': field['static_write_occurrences'],
            'unknown_direction_occurrences': field['unknown_direction_occurrences'],
            'known_store_pc': field['known_store_pc'],
            'candidate_access_pcs': [r['pc'] for r in field['accesses']],
            'modeled_inter_access_paths': len(field['consecutive_same_offset_spans']),
            'semantic_role': 'unverified',
            'matching_ps2_offset': None,
        })

    # Any unknown/unparsed ESI operand remains in the report; absence from
    # the simple-offset list MUST NOT be described as absence from the game.
    return {
        'phase': 45,
        'schema_version': SCHEMA_VERSION,
        'purpose': 'single verified Carbon PC steering evidence bundle',
        'source': {
            'platform': 'Carbon PC',
            'sha256': phase40['exe_sha256'],
            'steering_function_va': phase40['steering_function_va'],
            'verified_phase31_checks': phase40['phase31_verified_checks'],
            'function_length_bytes': STEERING_END - STEERING_START,
        },
        'verification': {
            'phase31_sha_and_anchor_gate': 'enforced_by_real_cli',
            'known_store_instruction_boundaries_checked': True,
            'complete_function_instruction_coverage_checked': True,
            'disassembly_engine': 'GNU objdump i386 intel',
            'source_binary_embedded_in_report': False,
            'ps2_to_pc_field_equivalence_verified': False,
            'runtime_gameplay_execution_observed': False,
            'steering_handling_patch_produced': False,
        },
        'overview': {
            'decoded_function_instructions': len(instructions),
            'known_store_anchor_count': len(stores),
            'simple_esi_memory_access_count': census['simple_esi_access_count'],
            'complex_esi_operand_count': census['complex_esi_operand_count'],
            'unparsed_memory_operand_form_count':
                census['unknown_memory_operand_form_count'],
            'candidate_offsets': overview,
        },
        'register_origin_evidence': stores,
        'candidate_path_evidence': {
            'anchor_to_anchor': phase44['anchor_to_anchor_cfg_path_evidence'],
            'candidates': phase44['candidate_offsets'],
            'cfg_issue_counts': phase44['cfg_issue_counts'],
        },
        'unresolved_address_forms': {
            'complex_esi_operands': census['complex_esi_operands'],
            'unparsed_memory_operand_forms': census['unparsed_memory_operand_forms'],
        },
        'manual_next_steps': [
            'Run this bundle only with the exact locally owned supported NFSC.exe.',
            'Inspect the source-register traces for unresolved definitions and calls.',
            'Check all static uses of +0x104/+0x118 and control-flow uncertainty.',
            'Establish actual object types and steering-state semantics separately.',
            'Compare PS2 steering values only after independent PC field verification.',
            'Test only a reversible, opt-in steering change after source-backed validation.',
        ],
        'limitations': [
            'Instruction order and modeled CFG paths do not establish real execution.',
            'ESI-relative offsets may refer to different objects on different paths.',
            'Unknown/derived/indexed memory operands can hide other accesses.',
            'Conservative register traces and CFG effects do not form a decompiler.',
            'The report does not prove lighter handling or any modified gameplay.',
        ],
    }


def audit_exact_source(data: bytes) -> dict:
    """The only production entrypoint: version gate before any disassembly."""
    verified = extract_from_verified_image(data)
    raw = at(data, sections(data), STEERING_START, STEERING_END - STEERING_START)
    instructions = disassemble(raw, STEERING_START)
    if (not instructions or instructions[0]['pc'] != STEERING_START
            or instructions[-1]['pc'] + instructions[-1]['length'] != STEERING_END):
        raise ValueError('incomplete steering-function disassembly')
    return review_from_decoded(instructions, verified)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='User-owned exact supported Carbon PC NFSC.exe')
    parser.add_argument('--output', type=Path, help='JSON report; stdout if omitted')
    parser.add_argument('--overwrite', action='store_true',
                        help='Explicitly replace an existing report, never the executable')
    args = parser.parse_args(argv)
    try:
        report = audit_exact_source(args.exe.read_bytes())
        text = json.dumps(report, indent=2) + '\n'
        if args.output:
            save_report(args.output, text, args.overwrite, args.exe)
            print('Phase 45 evidence report:', args.output)
        else:
            print(text, end='')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        parser.exit(1, f'FAIL (no changes to source executable): {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
