#!/usr/bin/env bash
# Reuse one authenticated native executable, never a prior guest state.
set -euo pipefail
umask 077
here="$(cd "$(dirname "$0")" && pwd)"
describe=0
if [[ $# == 1 && "$1" == --describe-mode ]]; then
  describe=1
elif [[ $# == 3 ]]; then
  exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
  [[ -f "$exe" && -x "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || exit 2
  mkdir -m 700 "$work"
else exit 2
fi
# Remove unrelated launcher overrides. Each lane has a fixed explicit
# contract, all three retain the same verified pre-second-IRQ sequence.
while IFS= read -r key; do
  [[ "$key" != UNDERCOVER_RUN_* ]] || unset "$key"
done < <(compgen -e)
common=(
  UNDERCOVER_RUN_V919_HANDLER_EPILOGUE=1 UNDERCOVER_RUN_V920_HANDLER_RETURN=1
  UNDERCOVER_RUN_V921_CAPTURE_JOIN=1 UNDERCOVER_RUN_V922_IRQ_RETURN=1
  UNDERCOVER_RUN_V932_PENDING_RFI=1 UNDERCOVER_RUN_V939_SECOND_VECTOR=1
  UNDERCOVER_RUN_V951_SECOND_DISPATCH=1 UNDERCOVER_RUN_V958_SECOND_ACK=1
  UNDERCOVER_RUN_V967_POST_ACK=1 UNDERCOVER_RUN_V989_SHARED_COMPLETION=1
)
success=(UNDERCOVER_RUN_V975_SECOND_TIME=1 UNDERCOVER_RUN_V981_SECOND_FRONTIER=1
  UNDERCOVER_RUN_V995_SUCCESS_FRONTIER=1 UNDERCOVER_RUN_V1009_SECOND_CALLBACK=1
  UNDERCOVER_RUN_V1012_SI_PROFILE=port1-present)
failed=0
for lane in absent mixed-prefix mixed-time; do
  case "$lane" in
    absent) flags=(UNDERCOVER_RUN_V1015_ERROR_COMPLETION=1 UNDERCOVER_RUN_V1012_SI_PROFILE=absent);;
    mixed-prefix) flags=("${success[@]}");;
    mixed-time) flags=("${success[@]}" UNDERCOVER_RUN_V1014_SECOND_CALLBACK_TIME=1);;
  esac
  echo "V1018_LANE_BEGIN lane=$lane"
  rc=0
  if [[ "$describe" == 1 ]]; then
    env "${common[@]}" "${flags[@]}" bash "$here/run_v575_dsp_sc_launch.sh" --describe-mode irq-si-handler-suffix || rc=$?
  else
    env "${common[@]}" "${flags[@]}" bash "$here/run_v575_dsp_sc_launch.sh" "$exe" "$dol" "$work/$lane" irq-si-handler-suffix || rc=$?
  fi
  if [[ "$rc" != 0 ]]; then failed=$((failed+1));fi
  echo "V1018_LANE_END lane=$lane audit_rc=$rc boot_verified=0"
done
echo "V1018_MATRIX_RESULT attempted=3 failed=$failed describe=$describe boot_verified=0"
[[ "$failed" == 0 ]]
