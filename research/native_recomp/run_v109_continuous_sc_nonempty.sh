#!/usr/bin/env bash
# V109: execute original nonempty SYSCONF pathname second copy privately.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v109_continuous_sc_nonempty.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/derive_v109_sc_nonempty_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh"
echo 'V109_WRAPPER derived'
bash -n "$work/run.sh"
echo 'V109_WRAPPER syntax_ok'
V109_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
