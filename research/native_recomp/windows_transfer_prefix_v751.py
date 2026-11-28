#!/usr/bin/env python3
"""Windows full-image original SI transfer prefix, stopping before MMIO.

Reuse the authenticated V742 time return and the existing V768 original
transfer prefix. This is not a complete SI transaction or game boot.
"""
from __future__ import annotations
import re
from typing import NamedTuple
from audit_v742_handler_time import RESULT as TIME_RESULT, diagnostic as time_diagnostic
from audit_v768_transfer_prefix import (
    ENTRY, RESULT, inspect as audit_transfer,
)
from windows_startup_scope_v434 import MAX_LOG, audit as audit_time


class TransferPlan(NamedTuple):
    env: dict[str, str]
    analyzer: tuple[str, ...]
    observers: tuple[tuple[str, str], ...]


def plan(scope: str, synthetic: bool, prefix: bool, time_suffix: bool,
         returned: bool = False, suffix: bool = False,
         alarm: bool = False, alarm_suffix: bool = False,
         callback_prefix: bool = False, callback_time: bool = False,
         callback_frontier: bool = False, wireless_wrapper: bool = False, wireless_write: bool = False, combined_callback: bool = False, handler_return: bool = False) -> TransferPlan:
    """One contract for source ownership, observer order and launch flags."""
    if any(type(x) is not bool for x in (synthetic, prefix, time_suffix, returned, suffix, alarm, alarm_suffix, callback_prefix, callback_time, callback_frontier, wireless_wrapper, wireless_write, combined_callback, handler_return)):
        raise ValueError('transfer option')
    if not prefix and not returned and not suffix and not alarm and not alarm_suffix and not callback_prefix and not callback_time and not callback_frontier and not wireless_wrapper and not wireless_write and not combined_callback and not handler_return:
        return TransferPlan({}, (), ())
    if synthetic or scope != 'os-si-handler-time' or time_suffix or sum((prefix, returned, suffix, alarm, alarm_suffix, callback_prefix, callback_time, callback_frontier, wireless_wrapper, wireless_write, combined_callback, handler_return)) != 1:
        raise ValueError('transfer scope')
    # Match the existing Linux full-image translation contract. The
    # analyzer owns the original transfer root and compiler save alias;
    # V777 also needs the authenticated compiler restore alias.
    analyzer = ('--transfer-prefix',)
    observers = (('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),)
    env = {'UNDERCOVER_V747_TIME_SUFFIX': '1'}
    if returned or suffix or alarm or alarm_suffix or callback_prefix or callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
        analyzer += ('--transfer-return',)
        observers += (('transfer_return_observer', 'prepare_v777_transfer_return.py'),)
        env['UNDERCOVER_V777_TRANSFER_RETURN'] = '1'
        if suffix or alarm or alarm_suffix or callback_prefix or callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            observers += (('transfer_suffix_observer', 'prepare_v778_transfer_suffix.py'),)
            env['UNDERCOVER_V778_TRANSFER_SUFFIX'] = '1'
        if alarm or alarm_suffix or callback_prefix or callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            analyzer += ('--alarm',)
            observers += (('alarm_return_observer', 'prepare_v786_alarm_return.py'),)
            env['UNDERCOVER_V786_ALARM_RETURN'] = '1'
        if alarm_suffix or callback_prefix or callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            observers += (('alarm_suffix_observer', 'prepare_v789_alarm_suffix.py'),)
            env['UNDERCOVER_V789_ALARM_SUFFIX'] = '1'
        if callback_prefix or callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            analyzer += ('--callback-prefix',)
            observers += (('callback_prefix_observer', 'prepare_v807_callback_prefix.py'),)
            env['UNDERCOVER_V807_CALLBACK_PREFIX'] = '1'
        if callback_time or callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            observers += (('callback_time_observer', 'prepare_v813_callback_time.py'),)
            env['UNDERCOVER_V813_CALLBACK_TIME'] = '1'
        if callback_frontier or wireless_wrapper or wireless_write or combined_callback or handler_return:
            observers += (('callback_frontier_observer', 'prepare_v831_callback_frontier.py'),)
            env['UNDERCOVER_V831_CALLBACK_FRONTIER'] = '1'
        if wireless_wrapper or wireless_write or combined_callback or handler_return:
            observers += (('wireless_wrapper_observer', 'prepare_v847_wireless_wrapper.py'),)
            env['UNDERCOVER_V847_WIRELESS'] = '1'
        if wireless_write or combined_callback or handler_return:
            observers += (('wireless_write_observer', 'prepare_v861_wireless_write.py'),)
            env['UNDERCOVER_V861_WIRELESS_WRITE'] = '1'
        if combined_callback or handler_return:
            observers += (('combined_callback_observer', 'prepare_v863_combined_callback.py'),)
            env['UNDERCOVER_V850_CALLBACK_RETURN'] = '1'
        if handler_return:
            # Include the authenticated original scheduler and RFI loader
            # in the same full-image translation, but do not execute them.
            analyzer += ('--epilogue',)
            observers += (
                ('handler_suffix_observer', 'prepare_v868_handler_suffix.py'),
                ('handler_epilogue_observer', 'prepare_v919_handler_epilogue.py'),
                ('handler_dispatch_return_observer', 'prepare_v920_handler_return.py'),
            )
            env.update(UNDERCOVER_V868_HANDLER_SUFFIX='1',
                       UNDERCOVER_V919_HANDLER_EPILOGUE='1',
                       UNDERCOVER_V920_HANDLER_RETURN='1')
    else:
        env['UNDERCOVER_V768_TRANSFER_PREFIX'] = '1'
    return TransferPlan(env, analyzer, observers)


def launch_overlay(scope: str, synthetic: bool, enabled: bool,
                   time_suffix: bool) -> dict[str, str]:
    """Compatibility wrapper for the independent prefix-only contract."""
    return plan(scope, synthetic, enabled, time_suffix).env


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('transfer log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows) if re.fullmatch(TIME_RESULT, line)]
    time_ok = False
    tail_ok = False
    transfer_ok = False
    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(l.startswith(b'V768_') for l in before):
            _, time_ok = audit_time(b'\n'.join(before) + b'\n', 0,
                                    'os-si-handler-time')
        # The guest reaches the original transfer prologue, saves GPRs,
        # disables interrupts, then stops before the next unadmitted call or MMIO.
        # Nothing else is permitted after the authenticated time return.
        tail_ok = (len(tail) == 2 and
                   re.fullmatch(ENTRY, tail[0]) is not None and
                   re.fullmatch(RESULT, tail[1]) is not None)
        if time_ok and tail_ok and rc == 0 and not timed_out:
            _, transfer_ok = audit_transfer(raw, rc)
    ok = bool(time_ok and tail_ok and transfer_ok and
              rc == 0 and not timed_out)
    return (
        'V751_WINDOWS_TRANSFER exit=' +
        ('timeout' if timed_out else
         'zero' if rc == 0 else
         'exception' if rc < 0 or rc >= 0xC0000000 else 'other') +
        f' time_verified={int(time_ok)} transfer_prefix_verified={int(ok)}'
        ' mmio_executed=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        time_diagnostic(line) or re.fullmatch(ENTRY, line) is not None or
        re.fullmatch(RESULT, line) is not None or
        re.fullmatch(
            rb'V768_TRANSFER_INVALID kind=[1-6] reason=[0-7] stage=[0-3]'
            rb' visits=[0-9]{1,3} trace=[0-9]{1,2}', line) is not None
    )
