#!/usr/bin/env bash
# V115 original nonempty SC request through the original syscall vector to IOS IRQ-disable entry.
set -euo pipefail
if (( $# != 2 ));then echo 'usage: run_v115_continuous_sc_irq_disable.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2;exit 2;fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/derive_v115_sc_irq_disable_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh"
echo 'V110_WRAPPER derived'
if ! bash -n "$work/run.sh" 2>"$work/runner-parse.log";then
  echo 'V110_WRAPPER syntax_failed' >&2
  line="$(grep -Eo 'line [0-9]+' "$work/runner-parse.log" | head -n 1 || true)"
  if [[ "$line" =~ ^line[[:space:]][0-9]+$ ]]; then
    echo "V110_WRAPPER_SYNTAX $line" >&2
  fi
  exit 1
fi
echo 'V110_WRAPPER syntax_ok'
V110_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
