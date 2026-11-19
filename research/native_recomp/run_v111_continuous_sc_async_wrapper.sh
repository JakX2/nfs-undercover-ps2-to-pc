#!/usr/bin/env bash
# V111 original nonempty SC wrapper to IOS_OpenAsync entry.
set -euo pipefail
if (( $# != 2 ));then echo 'usage: run_v111_continuous_sc_async_wrapper.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2;exit 2;fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/derive_v111_sc_async_wrapper_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh"
bash -n "$work/run.sh"
V110_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
