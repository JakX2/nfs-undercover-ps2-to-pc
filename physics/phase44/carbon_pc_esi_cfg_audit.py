#!/usr/bin/env python3
"""Phase 44: bounded x86 control-flow path audit for Carbon PC steering.

Verification is delegated to Phase42 (exact SHA, PE/calls/bytes), and Phase43
checks instruction boundaries/census agreement. This tool never calls the game,
writes its executable, asserts object identity, or compares PS2 field offsets.
"""
from __future__ import annotations

import argparse
from collections import deque
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
    branch_target, describe_effect, disassemble,
)
from physics.phase42.carbon_pc_esi_access_census import audit_verified_pc  # noqa: E402
from physics.phase43.carbon_pc_candidate_access_review import (  # noqa: E402
    build_review, validate_instructions,
)

# State describes instructions encountered, not whether ESI's numeric value
# actually differs: a write can legitimately restore the previous value.
UNCHANGED = 'no_detected_esi_write'
REDEFINED = 'esi_definition_seen'
UNKNOWN = 'unknown_esi_effect'
STATES = (UNCHANGED, REDEFINED, UNKNOWN)
MAX_INSTRUCTIONS = 4096
MAX_GRAPH_STATES = MAX_INSTRUCTIONS * len(STATES)

# Only direct near jumps and simple conditionals are given modeled successors.
# Indirect transfers and less common control forms are explicitly unresolved.
CONDITIONAL = frozenset((
    'ja', 'jae', 'jb', 'jbe', 'jc', 'jcxz', 'jecxz', 'je', 'jg', 'jge',
    'jl', 'jle', 'jna', 'jnae', 'jnb', 'jnbe', 'jnc', 'jne',
    'jng', 'jnge', 'jnl', 'jnle', 'jno', 'jnp', 'jns', 'jnz',
    'jo', 'jp', 'jpe', 'jpo', 'js', 'jz',
    'loop', 'loope', 'loopne', 'loopz', 'loopnz',
))
RETURNS = frozenset(('ret', 'retn', 'retf', 'iret', 'iretd'))
TRAPS = frozenset(('int', 'int3', 'into', 'ud2', 'syscall', 'sysenter'))


def _control_successors(ins: dict, following: int | None,
                        valid_pcs: set[int], lower: int, upper: int) -> tuple[tuple[int, ...], str | None]:
    """(known successors, unresolved/exit reason). Never invent a jump edge."""
    name = ins['mnemonic'].lower()
    if name in RETURNS or name in TRAPS:
        return (), 'terminal_exit'
    if name.startswith('call'):
        # Continue at the known next instruction but taint ESI; no subroutine
        # dataflow/calling convention assumptions are made here.
        return ((following,) if following is not None else ()), 'call_unmodeled_effect'
    if name in ('jmp', 'ljmp') or name in CONDITIONAL:
        target = branch_target(ins)
        if target is None:
            return ((following,) if name in CONDITIONAL and following is not None else ()), 'unresolved_branch_target'
        if lower <= target < upper and target not in valid_pcs:
            raise ValueError(f'branch into undecoded x86 instruction at {target:#x}')
        nexts = []
        if target in valid_pcs:
            nexts.append(target)
        if name in CONDITIONAL and following is not None and following not in nexts:
            nexts.append(following)
        return tuple(nexts), ('branch_exits_function' if target not in valid_pcs else None)
    if name.startswith('j') or name.startswith('loop'):
        return (), 'unsupported_control_transfer'
    return ((following,) if following is not None else ()), None


def build_cfg(instructions: list[dict]) -> dict:
    """Build a finite, edge-explicit x86 CFG from fully bounded instruction PCs."""
    index = validate_instructions(instructions)
    if len(index) > MAX_INSTRUCTIONS:
        raise ValueError('too many instructions for bounded static CFG')
    start = instructions[0]['pc']
    end = instructions[-1]['pc'] + instructions[-1]['length']
    valid = set(index)
    graph = {}
    exits = {}
    for i, ins in enumerate(instructions):
        nextpc = instructions[i + 1]['pc'] if i + 1 < len(instructions) else None
        edges, issue = _control_successors(ins, nextpc, valid, start, end)
        graph[ins['pc']] = edges
        if issue:
            exits[ins['pc']] = issue
    return {'edges': graph, 'issues': exits, 'start': start, 'end': end,
            'instructions': index}


def apply_effect(state: str, effect_kind: str) -> str:
    """Propagate coarse may-write information; never 'heal' previous hazards."""
    if state not in STATES:
        raise ValueError('invalid abstract state')
    if effect_kind.startswith('skip_'):
        return state
    if state == UNKNOWN:
        return UNKNOWN
    if effect_kind in ('opaque_barrier', 'partial_register_write_unknown',
                       'partial_register_source_unknown',
                       'implicit_register_definition_unknown',
                       'address_expression_unresolved',
                       'arithmetic_definition_unresolved',
                       'other_definition_unresolved'):
        return UNKNOWN
    if effect_kind in ('register_copy', 'memory_load_unknown_value',
                       'immediate_or_symbol', 'known_zero'):
        return REDEFINED
    if effect_kind == 'control_flow_barrier':
        return state
    return UNKNOWN


def audit_paths(cfg: dict, earlier: int, later: int) -> dict:
    """Explore each abstract route from just before earlier to just before later.

    A clean modeled route is not an object-identity proof. Unknown jumps,
    calls and branches are recorded separately, including off-range exits.
    """
    index = cfg['instructions']
    if earlier not in index or later not in index or earlier >= later:
        raise ValueError('expected ordered, decoded x86 instruction PCs')
    queue = deque([(earlier, UNCHANGED)])
    seen = set()
    outcomes = set()
    hazards = set()
    examined = 0
    while queue:
        pc, state = queue.popleft()
        if (pc, state) in seen:
            continue
        seen.add((pc, state))
        examined += 1
        if examined > MAX_GRAPH_STATES:
            raise ValueError('static graph-state budget exceeded')
        if pc == later:
            outcomes.add(state)
            continue
        ins = index[pc]
        kind = describe_effect(ins, 'esi')['kind']
        updated = apply_effect(state, kind)
        issue = cfg['issues'].get(pc)
        if issue:
            hazards.add(issue)
        if issue == 'call_unmodeled_effect':
            updated = UNKNOWN
        # An unresolved branch successor might re-enter the function later.
        # Report the uncertainty, never invent a synthetic edge.
        for successor in cfg['edges'][pc]:
            queue.append((successor, updated))
    labels = [x for x in STATES if x in outcomes]
    return {
        'earlier_pc': f'0x{earlier:08X}', 'later_pc': f'0x{later:08X}',
        'modeled_routes_to_target': bool(outcomes),
        'modeled_target_states': labels,
        'route_with_no_detected_esi_write': UNCHANGED in outcomes,
        'route_with_esi_definition': REDEFINED in outcomes,
        'route_with_uncertain_esi_effect': UNKNOWN in outcomes,
        'unresolved_or_exiting_controls_encountered': sorted(hazards),
        'explored_static_states': examined,
        'same_runtime_object_proven': False,
        'real_execution_observed': False,
    }


def augment_review(instructions: list[dict], review: dict) -> dict:
    """Add abstract path evidence to Phase43's already verified structure."""
    cfg = build_cfg(instructions)
    enhanced = []
    for item in review['candidate_offsets']:
        spans = []
        for span in item['consecutive_same_offset_spans']:
            earlier = int(span['earlier_pc'], 16)
            later = int(span['later_pc'], 16)
            spans.append({**span, 'cfg_path_evidence': audit_paths(cfg, earlier, later)})
        enhanced.append({**item, 'consecutive_same_offset_spans': spans})
    return {
        'phase': 44, 'source_sha256': review.get('source_sha256'),
        'scope': 'static modeled x86 paths over candidate ESI-relative memory accesses',
        'function_instruction_count': len(instructions),
        'cfg_instruction_count': len(cfg['edges']),
        'cfg_issue_counts': {
            reason: sum(x == reason for x in cfg['issues'].values())
            for reason in sorted(set(cfg['issues'].values()))
        },
        'candidate_offsets': enhanced,
        'anchor_to_anchor_cfg_path_evidence': audit_paths(cfg, *ANCHOR_ADDRESSES),
        'semantic_field_names_verified': False,
        'ps2_to_pc_equivalence_verified': False,
        'runtime_object_identity_verified': False,
        'gameplay_patch_created': False,
        'limitations': [
            'CFG edges model direct branch targets; indirect and unsupported transfers are unresolved.',
            'Calls are modeled as unknown ESI effects on their continuation path.',
            'Instruction writes are conservative and not full semantic equivalence analysis.',
            'A modeled stable path does not prove that it executes or shares object identity.',
            'Other base registers and indirect indexed accesses are not analyzed.',
            'No original PS2/PC runtime physics or handling changes are established.',
        ],
    }


def audit_verified_image(data: bytes) -> dict:
    """Never perform disassembly before full Phase31/40/42 authentication."""
    census = audit_verified_pc(data)
    raw = at(data, sections(data), STEERING_START, STEERING_END - STEERING_START)
    instructions = disassemble(raw, STEERING_START)
    review = build_review(instructions, census)
    return augment_review(instructions, review)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='Exact supported user-owned Carbon PC NFSC.exe')
    parser.add_argument('--output', type=Path, help='JSON output, stdout by default')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = audit_verified_image(args.exe.read_bytes())
        output = json.dumps(report, indent=2) + '\n'
        if args.output:
            save_report(args.output, output, args.overwrite, args.exe)
            print('Phase 44 report saved:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        parser.exit(1, f'FAIL (no executable changes): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
