#!/usr/bin/env bash
# Bounded, original DOL-only, headless startup through the DSP flush return.
set -euo pipefail
umask 077
[[ $# == 3 || ( $# == 4 && ( "$4" == dsp-return || "$4" == mi-return || "$4" == report-return || "$4" == arena-return || "$4" == irq-enable-return ) ) ]] || exit 2
mode="${4:-dsp-sc}"
extra=();audit=audit_v575_dsp_sc_frontier.py
if [[ "$mode" == dsp-return || "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return ]]; then extra+=(UNDERCOVER_V581_DSP=1);audit=audit_v581_dsp_return.py;fi
if [[ "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return ]]; then extra+=(UNDERCOVER_V591_MI=1 UNDERCOVER_V612_MAPPING=1);audit=audit_v591_memory_init.py;fi
if [[ "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return ]]; then extra+=(UNDERCOVER_V603_REPORT=1);audit=audit_v603_boot_report.py;fi
if [[ "$mode" == arena-return || "$mode" == irq-enable-return ]]; then extra+=(UNDERCOVER_V609_ARENA=1);audit=audit_v609_arena_clear.py;fi
if [[ "$mode" == irq-enable-return ]]; then extra+=(UNDERCOVER_V616_IRQ=1);audit=audit_v616_irq_enable.py;fi
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$exe" && -x "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
python3 "$here/write_sram_profile_v536.py" "$work/exi-test-profile.txt"
printf '%s\n' UNDERCOVER_SI_PROFILE_V1 latency=00000008 port0=absent port1=absent port2=absent port3=absent > "$work/si-test-profile.txt"
echo 'V575_DSP_SC_INPUT accepted=1 dol_only=1 profiles=synthetic'
rc=0
(
  cd "$work"
  ulimit -c 0
  ulimit -f 8192
  timeout --signal=TERM --kill-after=3s 20s env -i PATH="$PATH" HOME="$work" \
    NWII_HEADLESS=1 NWII_TRACE_CALLS=1 UNDERCOVER_V419_START=1 \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    UNDERCOVER_V475_IRQ_MMIO=1 UNDERCOVER_V481_IRQ_BANKS=1 UNDERCOVER_V490_EXI_CONTROLLER=1 \
    "UNDERCOVER_V501_EXI_PROFILE=$work/exi-test-profile.txt" \
    UNDERCOVER_V512_SI=1 "UNDERCOVER_V518_SI_PROFILE=$work/si-test-profile.txt" \
    UNDERCOVER_V522_VICLK=0 UNDERCOVER_V537_ACR=1 UNDERCOVER_V574_SC=1 \
    "${extra[@]}" "$exe" "$dol" "$work/config.toml"
) > "$work/run-private.log" 2>&1 || rc=$?
audit_rc=0
python3 "$here/$audit" "$work/run-private.log" "$rc" || audit_rc=$?
# The longer chained audits deliberately emit only their own census. Export
# the same bounded mapper diagnostic if an upstream MI refusal stopped them.
if [[ "$rc" == 115 && "$audit" != audit_v591_memory_init.py ]]; then
  PYTHONPATH="$here" python3 - "$work/run-private.log" <<'PY'
import sys
from pathlib import Path
from audit_v591_memory_init import MAX_LOG,mapper_diagnostic
p=Path(sys.argv[1])
if p.stat().st_size<=MAX_LOG:
    row=mapper_diagnostic(p.read_bytes(),115)
    if row:print(row)
PY
fi
if [[ "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return ]]; then
  if [[ "$(grep -Fxc 'V612_MAPPING_PROFILE accepted=1 mem1=24 mem2=64 mapped_mem2=52 ipc_kib=512 synthetic=1' "$work/run-private.log" || true)" != 1 ]]; then echo "V612_MAPPING_LAUNCH verified=0";exit 1;fi
  echo "V612_MAPPING_LAUNCH verified=1"
fi
exit "$audit_rc"
