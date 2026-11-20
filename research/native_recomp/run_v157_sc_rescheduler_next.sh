#!/usr/bin/env bash
# V157 owner-original Wii SC ACK to authenticated PPC external vector.
set -euo pipefail
if (( $# != 2 ));then echo 'usage: run_v157_sc_rescheduler_next.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2;exit 2;fi
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
if ! python3 "$here/derive_v157_sc_rescheduler_next_runner.py" "$here/run_v79_continuous_reply_entry.sh" "$work/run.sh" 2>"$work/derive.log"; then
  python3 - "$work/derive.log" <<'PY'
from pathlib import Path
import sys
log=Path(sys.argv[1]).read_text(encoding="utf-8",errors="replace")
if "missing source anchor:" in log or "missing anchor:" in log or "anchor missing" in log:
    kind="missing_anchor"
elif "ambiguous" in log or "duplicated" in log or "not unique" in log:
    kind="ambiguous_anchor"
elif "SyntaxError" in log or "IndentationError" in log:
    kind="python_syntax"
elif "ModuleNotFoundError" in log or "ImportError" in log:
    kind="import_error"
elif "ValueError" in log:
    kind="other_value_error"
else:
    kind="other_error"
print("V157_DERIVATION result=failed kind="+kind,file=sys.stderr)
PY
  exit 1
fi
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
