#!/usr/bin/env bash
set -euo pipefail
if (( $# != 2 )); then echo 'usage: run_v107_sc_source_probe.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2; exit 2; fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 - "$here" "$work" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from derive_v107_sc_source_runner import derive
Path(sys.argv[2],"run.sh").write_text(derive(Path(sys.argv[1],"run_v79_continuous_reply_entry.sh").read_text()))
PY
bash -n "$work/run.sh"
V104_SOURCE_ROOT="$here" bash "$work/run.sh" "$1" "$2"
