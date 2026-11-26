#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 || ( $# == 3 && "$3" == --completion ) ]] || exit 2
umask 077
ulimit -c 0
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
d="$(realpath "$1")";e="$(realpath "$2")";out="$work/input"
python3 "$here/make_v1256_scheduler_fixture.py" "$d" "$e" "$out"
python3 "$here/prepare_v1259_scheduler_vector.py" "$d" "$e" "$out/v1259_private_vector.h"
for step in prepare_v1260_scheduler_vector prepare_v1261_ipc_dispatch prepare_v1266_joined_ack prepare_v1270_ipc_epilogue prepare_v1281_reply_fixture prepare_v1289_wake_fixture prepare_v1292_nested_wake prepare_v1316_reply_helper;do
    python3 "$here/$step.py" "$d" "$e" "$out"
done
python3 "$here/prepare_v1299_reply_return.py" "$d" "$e" "$out" --helper
python3 "$here/prepare_v1314_save_lane.py" "$d" "$e" "$out"
python3 "$here/prepare_v1321_combined_resume.py" "$d" "$e" "$out"
PYTHONPATH="$here" python3 "$here/verify_v1325_combined_preflight.py" "$d" "$e" "$out"

if [[ "${3-}" == --completion ]];then
  python3 "$here/prepare_v1337_open_completion.py" "$d" "$e" "$out"
fi
