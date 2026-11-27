#!/usr/bin/env python3
"""Build a bounded numeric-only original formatter continuation contract.

The caller must supply a separately authenticated predecessor fixture and
symbolic register state. All words and addresses remain owner-private.
This planner never executes or writes guest state.
"""
from typing import NamedTuple
from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from guarded_continuation import GUARD, check_spans
from prepare_formatter_caller_integer_contract import step

CAP = 16
MASK = 0xffffffff


class TailStep(NamedTuple):
    word: int
    inputs: tuple
    destination: int | None
    value: int


class TailPlan(NamedTuple):
    blocks: dict
    root: int
    first: int
    steps: tuple
    next_word: int
    return_pc: int
    stop_reason: str


def _word(value):
    return type(value) is int and 0 <= value <= MASK


def extend(sixth, live, original_words, *, cap=CAP):
    """Use exact 118–127 prefix and authentic 128 lookahead, no guesses.

    Returns None and a stop reason when the next original operation is
    not admissible. A successful plan contains one or more strictly
    contiguous numeric-only instructions and one unexecuted lookahead.
    The original guard is moved only inside the private returned fixture.
    """
    if (type(cap) is not int or not 1 <= cap <= CAP or
            not isinstance(sixth, tuple) or len(sixth) != 2 or
            not isinstance(sixth[0], dict) or
            not isinstance(sixth[1], tuple) or len(sixth[1]) != 8 or
            not isinstance(live, (tuple, list)) or len(live) != 32 or
            not isinstance(original_words, (tuple, list)) or
            not 11 <= len(original_words) <= 16384 or
            not all(_word(w) for w in original_words)):
        raise ValueError('tail contract geometry')
    blocks, fields = sixth
    if not all(_word(x) for x in fields):
        raise ValueError('tail contract fields')
    root, pc, word, first, next_word, dst, value, ret = fields
    body = blocks.get(root)
    if (not isinstance(body, tuple) or len(body) != 12 or
            root & 3 or not 0x80000000 <= root < 0x81800000 or
            pc != root + 36 or first != root + 40 or
            body[9:] != (word, next_word, GUARD) or
            next_word == GUARD or tuple(original_words[:11]) != body[:11] or
            dst not in (0, *range(3, 13)) or
            live[dst] != ('const', value) or
            ret & 3 or root <= ret < root + 48):
        raise ValueError('tail predecessor mismatch')
    try:
        check_spans({address: 4 * len(words) for address, words in blocks.items()})
    except (TypeError, KeyError, ValueError) as error:
        raise ValueError('tail predecessor geometry') from error

    gp = tuple(live)
    rows = []
    reason = 'cap'
    for i in range(10, min(10 + cap, len(original_words) - 1)):
        instruction = original_words[i]
        if instruction == GUARD:
            reason = 'guard'; break
        if boundary_shape(instruction) != 'integer':
            reason = 'non_integer'; break
        _, reads, writes, _, carry, xer, oe = classify(instruction)
        if carry or xer or oe or len(set(reads)) > 3 or len(writes) > 1:
            reason = 'integer_effects'; break
        # The bounded C++ observer permits numeric operands and volatile
        # writes only. Never infer a numeric stack pointer or saved register.
        try:
            after, inputs = step(instruction, gp)
        except (ValueError, TypeError, IndexError, KeyError) as error:
            reason = (str(error).replace(' ', '_') if str(error) in {
                'caller integer opcode', 'caller integer encoding',
                'caller integer effects', 'caller integer inputs',
                'caller integer registers',
            } else 'not_modelled')
            break
        if len(after) != 32:
            raise ValueError('tail symbolic state')
        dest = writes[0] if writes else None
        result = after[dest] if dest is not None else ('const', 0)
        if (result[0] != 'const' or not _word(result[1]) or
                tuple(r for r, _ in inputs) != tuple(sorted(set(reads)))):
            raise ValueError('tail symbolic effect')
        rows.append(TailStep(instruction, inputs, dest, result[1]))
        gp = after
    else:
        if len(rows) < cap:
            reason = 'function_end'
    if not rows:
        return None, reason
    end = 10 + len(rows)
    lookahead = original_words[end]
    if lookahead == GUARD:
        raise ValueError('tail lookahead guard')
    new_body = tuple(original_words[:end + 1]) + (GUARD,)
    if (root + 4 * len(new_body) > 0x81800000 or
            root <= ret < root + 4 * len(new_body)):
        raise ValueError('tail return or memory alias')
    out = {**blocks, root: new_body}
    try:
        check_spans({address: 4 * len(words) for address, words in out.items()})
    except (TypeError, KeyError, ValueError) as error:
        raise ValueError('tail sibling overlap') from error
    return TailPlan(out, root, first, tuple(rows), lookahead, ret, reason), reason
