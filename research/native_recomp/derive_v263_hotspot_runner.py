#!/usr/bin/env python3
"""V263 flat process boundary: reuse V262 runner without recursive imports.

V262 already generates the complete original-game execution and all sixteen
authentic test gates. V263 invokes V262 in a child Python interpreter and
appends one read-only private-log analysis, keeping the historical import
stack out of the current interpreter.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
DONE = "echo 'V262_IPC_STATE verified=1'"
EXTRA = '''
python3 "$V110_SOURCE_ROOT/analyze_v263_hotspot.py" "$work/v250-native.log"
echo 'V263_HOTSPOT verified=1'
'''


def derive_shell(source: str) -> str:
    if source.count(DONE) != 1:
        raise ValueError("V263 inherited V262 original-native milestone changed")
    return source.replace(DONE, DONE + EXTRA, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="v263-flat-runner-") as td:
        intermediate = Path(td) / "v262.sh"
        process = subprocess.run([
            sys.executable, str(HERE / "derive_v262_ipc_state_runner.py"),
            str(args.source), str(intermediate),
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            check=False)
        if process.returncode != 0:
            raise RuntimeError("V263 inherited V262 source-only generation failed")
        # The generated script contains no proprietary bytes. No guest code
        # is executed by this Python runner.
        derived = derive_shell(intermediate.read_text(encoding="utf-8"))
        with args.output.open("x", encoding="utf-8") as out:
            out.write(derived)
    return 0


if __name__ == "__main__":
    sys.exit(main())
