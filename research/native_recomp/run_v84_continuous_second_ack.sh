#!/usr/bin/env bash
# V84: second original STM Open -> native IOS ACK before second sleep.
# Use the verified V79 build chain without publishing private artifacts.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v84_continuous_second_ack.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/derive_v84_second_ack_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh"
bash -n "$work/run.sh"
V84_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
