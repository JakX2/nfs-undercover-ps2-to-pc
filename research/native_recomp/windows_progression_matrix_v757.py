#!/usr/bin/env python3
"""Same complete original Wii Windows executable through successive SI gates.

The translated private DOL, pinned runtime, and installed native observers
are identical across all launches. Every native process starts with fresh
guest/host state. Print only strict, allowlisted evidence and refusal codes.
No successful handler return, game main, first frame or gameplay is claimed.
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


# The complete native image must have all the previously authenticated
# originals installed; only the guest exit boundary changes per launch.
REQUIRED = ('UNDERCOVER_V747_TIME_SUFFIX',
            'UNDERCOVER_V777_TRANSFER_RETURN',
            'UNDERCOVER_V778_TRANSFER_SUFFIX',
            'UNDERCOVER_V786_ALARM_RETURN',
            'UNDERCOVER_V789_ALARM_SUFFIX',
            'UNDERCOVER_V807_CALLBACK_PREFIX',
            'UNDERCOVER_V813_CALLBACK_TIME')
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
    if len(STAGES) != 6 or len({s.name for s in STAGES}) != 6:
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
    report('V757_WINDOWS_PROGRESSION completed=6 full_image=1'
           ' compiler_reused=1 native=1 handler_return=0 boot_verified=0')
