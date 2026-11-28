#!/usr/bin/env python3
"""Same complete original Wii Windows executable through successive SI gates.

The translated private DOL, pinned runtime, and installed native observers
are identical across all launches. Every native process starts with fresh
guest/host state. Print only strict, allowlisted evidence and refusal codes.
No game main, first frame or gameplay is claimed; RFI remains unverified.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from windows_startup_scope_v434 import MAX_LOG
from windows_transfer_return_v752 import inspect as check_transfer, diagnostic as diag_transfer
from windows_transfer_suffix_v753 import inspect as check_suffix, diagnostic as diag_suffix
from windows_alarm_return_v754 import inspect as check_alarm, diagnostic as diag_alarm
from windows_alarm_suffix_v755 import inspect as check_alarm_suffix, diagnostic as diag_alarm_suffix
from windows_callback_prefix_v756 import inspect as check_callback, diagnostic as diag_callback
from windows_callback_time_v758 import inspect as check_time, diagnostic as diag_time
from windows_callback_frontier_v759 import inspect as check_frontier, diagnostic as diag_frontier
from windows_wireless_wrapper_v760 import inspect as check_wireless, diagnostic as diag_wireless
from windows_wireless_write_v761 import inspect as check_write, diagnostic as diag_write
from windows_combined_callback_v762 import inspect_completed as check_combined, diagnostic as diag_combined
from windows_handler_return_v763 import inspect as check_handler, diagnostic as diag_handler
from windows_scheduler_entry_v922 import inspect as check_scheduler, diagnostic as diag_scheduler
from windows_scheduler_return_v923 import inspect as check_scheduler_return, diagnostic as diag_scheduler_return


# The complete native image must have all the previously authenticated
# originals installed; only the guest exit boundary changes per launch.
REQUIRED = ('UNDERCOVER_V747_TIME_SUFFIX',
            'UNDERCOVER_V777_TRANSFER_RETURN',
            'UNDERCOVER_V778_TRANSFER_SUFFIX',
            'UNDERCOVER_V786_ALARM_RETURN',
            'UNDERCOVER_V789_ALARM_SUFFIX',
            'UNDERCOVER_V807_CALLBACK_PREFIX',
            'UNDERCOVER_V813_CALLBACK_TIME',
            'UNDERCOVER_V831_CALLBACK_FRONTIER',
            'UNDERCOVER_V847_WIRELESS',
            'UNDERCOVER_V861_WIRELESS_WRITE',
            'UNDERCOVER_V850_CALLBACK_RETURN',
            'UNDERCOVER_V868_HANDLER_SUFFIX',
            'UNDERCOVER_V919_HANDLER_EPILOGUE',
            'UNDERCOVER_V920_HANDLER_RETURN',
            'UNDERCOVER_V922_SCHEDULER_ENTRY',
            'UNDERCOVER_V923_SCHEDULER_RETURN')
OPTIONAL = REQUIRED[2:]


@dataclass(frozen=True)
class Stage:
    name: str
    enable: tuple[str, ...]
    auditor: Callable[[bytes, int, bool], tuple[str, bool]]
    diagnostic: Callable[[bytes], bool]


STAGES = (
    Stage('transfer-return', (), check_transfer, diag_transfer),
    Stage('transfer-suffix', OPTIONAL[:1], check_suffix, diag_suffix),
    Stage('alarm-return', OPTIONAL[:2], check_alarm, diag_alarm),
    Stage('alarm-suffix', OPTIONAL[:3], check_alarm_suffix, diag_alarm_suffix),
    Stage('callback-prefix', OPTIONAL[:4], check_callback, diag_callback),
    Stage('callback-time', OPTIONAL[:5], check_time, diag_time),
    Stage('callback-frontier', OPTIONAL[:6], check_frontier, diag_frontier),
    Stage('wireless-wrapper', OPTIONAL[:7], check_wireless, diag_wireless),
    Stage('wireless-write', OPTIONAL[:8], check_write, diag_write),
    Stage('combined-callback', OPTIONAL[:9], check_combined, diag_combined),
    Stage('handler-return', OPTIONAL[:12], check_handler, diag_handler),
    Stage('scheduler-entry', OPTIONAL[:13], check_scheduler, diag_scheduler),
    Stage('scheduler-return', OPTIONAL[:14], check_scheduler_return, diag_scheduler_return),
)


class ProgressionFailure(Exception):
    """Fixed public stage label; do not attach owner paths, PCs or words."""


def stage_environment(base: dict[str, str], stage: Stage) -> dict[str, str]:
    if (type(base) is not dict or type(stage) is not Stage or stage not in STAGES
            or any(base.get(key) != '1' for key in REQUIRED)):
        raise ValueError('original progression environment')
    output = dict(base)
    # Omit flags instead of writing 0, to test the default-disabled path.
    for key in OPTIONAL:
        output.pop(key, None)
    for key in stage.enable:
        output[key] = '1'
    return output


def run(exe: Path, dol: Path, config: Path, launch: Path,
        environment: dict[str, str], command: Callable[..., int],
        report: Callable[[str], None] = print) -> None:
    if any(not isinstance(x, Path) for x in (exe, dol, config, launch)):
        raise ValueError('original progression inputs')
    if not launch.is_dir() or not callable(command) or not callable(report):
        raise ValueError('original progression runtime')
    if len(STAGES) != 13 or len({s.name for s in STAGES}) != 13:
        raise ValueError('original progression stages')
    for stage in STAGES:
        log = launch / ('progression-' + stage.name + '.log')
        if log.exists() or log.is_symlink():
            raise ProgressionFailure(stage.name)
        timeout_status: dict[str, bool] = {}
        env = stage_environment(environment, stage)
        rc = command([exe, dol, config], log, 20, env=env, cwd=launch,
                     timeout_status=timeout_status)
        timeout = timeout_status.get('expired')
        ok = False
        row = ''
        raw = b''
        if (type(rc) is int and type(timeout) is bool and log.is_file()
                and not log.is_symlink() and log.stat().st_size <= MAX_LOG):
            raw = log.read_bytes()
            row, ok = stage.auditor(raw, rc, timeout)
        if row:
            report(row)
        if not ok:
            # Print only exactly recognized, bounded diagnostic refusal
            # markers, never raw owner output, instructions or guest state.
            for line in raw.splitlines():
                if b'_INVALID ' in line and stage.diagnostic(line) and len(line) <= 256:
                    report(line.decode('ascii'))
        # Always leave the redacted verdict as the final stage marker,
        # including after a known original instruction/MMIO refusal.
        report('V757_WINDOWS_PROGRESSION stage=' + stage.name
               + ' verified=' + str(int(ok)) + ' boot_verified=0')
        if not ok:
            raise ProgressionFailure(stage.name)
    report('V757_WINDOWS_PROGRESSION completed=13 full_image=1'
           ' compiler_reused=1 native=1 handler_return=1 scheduler_entry=1'
           ' scheduler_return=1 rfi=0 boot_verified=0')
