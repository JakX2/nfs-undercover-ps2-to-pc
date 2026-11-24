#!/usr/bin/env bash
# Bounded DOL-only launch of a private whole-image native executable.
set -euo pipefail
umask 077
if [[ $# -ne 3 && $# -ne 4 ]]; then
  echo 'Usage: run_private_full_start.sh PRIVATE_EXE OWNER_DOL FRESH_PRIVATE_RUN_DIR [startup|hardware|cache|data|os-entry|os-time|os-hardware|os-arena|os-ipc|os-vector|os-pack|os-alarm|os-irq|os-mmio|os-irq-return|os-context|os-cache-reuse|os-exi-poll]' >&2
  exit 2
fi
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
mode="${4:-startup}"
case "$mode" in
  startup) audit=audit_v419_full_start.py;;
  hardware) audit=audit_v425_full_hardware.py;;
  cache) audit=audit_v428_full_cache.py;;
  data) audit=audit_v430_full_data.py;;
  os-entry) audit=audit_v433_full_os_entry.py;;
  os-time) audit=audit_v435_full_os_time.py;;
  os-hardware) audit=audit_v439_full_os_hardware.py;;
  os-arena) audit=audit_v444_full_os_arena.py;;
  os-ipc) audit=audit_v446_full_os_ipc.py;;
  os-vector) audit=audit_v457_exception_vector.py;;
  os-pack) audit=audit_v466_exception_pack.py;;
  os-alarm) audit=audit_v470_alarm_startup.py;;
  os-irq) audit=audit_v473_module_irq.py;;
  os-mmio) audit=audit_v476_irq_mmio.py;;
  os-irq-return) audit=audit_v483_irq_return.py;;
  os-context) audit=audit_v486_context_startup.py;;
  os-cache-reuse) audit=audit_v488_os_cache_reuse.py;;
  os-exi-poll) audit=audit_v491_exi_poll.py;;
  *) echo 'Invalid bounded startup mode' >&2; exit 2;;
esac
[[ -x "$exe" && -f "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || {
  echo 'V419_FULL_START_INPUT accepted=0'; exit 1;
}
if [[ "$(sha256sum "$dol" | cut -d ' ' -f1)" != 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]]; then
  echo 'V419_FULL_START_INPUT accepted=0'; exit 1
fi
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
echo 'V419_FULL_START_INPUT accepted=1 dol_only=1'
extra_env=()
if [[ "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll ]]; then extra_env+=(UNDERCOVER_V475_IRQ_MMIO=1); fi
if [[ "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll ]]; then extra_env+=(UNDERCOVER_V481_IRQ_BANKS=1); fi
if [[ "$mode" == os-exi-poll ]]; then extra_env+=(UNDERCOVER_V490_EXI_CONTROLLER=1); fi
rc=0
(
  cd "$work"
  ulimit -c 0
  ulimit -f 8192
  timeout --signal=TERM --kill-after=3s 20s env -i PATH="$PATH" HOME="$work" \
    NWII_HEADLESS=1 NWII_TRACE_CALLS=1 UNDERCOVER_V419_START=1 \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "${extra_env[@]}" "$exe" "$dol" "$work/config.toml"
) > "$work/run-private.log" 2>&1 || rc=$?
python3 "$here/$audit" "$work/run-private.log" "$rc"
