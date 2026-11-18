#!/usr/bin/env bash
# V99: deferred native STM event ACK -> original STM return to OSInit.
# Use the verified V79 build chain without publishing private artifacts.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v99_continuous_post_nand.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/derive_v99_post_nand_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh"
bash -n "$work/run.sh"
V99_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
