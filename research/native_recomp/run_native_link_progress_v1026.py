#!/usr/bin/env python3
"""Report numeric Ninja build progress; private compiler output never escapes."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

LIMIT=65536
STATUS=re.compile(rb'^V1026_NINJA ([0-9]{1,7})/([0-9]{1,7}) ')
def progress(log):
    with log.open('rb') as f:
        size=f.seek(0,2)
        f.seek(max(0,size-LIMIT))
        data=f.read(LIMIT)
    rows=data.splitlines()
    if size>LIMIT:rows=rows[1:]
    for row in reversed(rows):
        m=STATUS.match(row)
        if m:
            done,total=map(int,m.groups())
            if 0<=done<=total and total>0:return done,total
    return None

def run(build):
    if not build.is_dir() or build.is_symlink():return 2
    log=build/'build-private.log'
    env=os.environ.copy();env['NINJA_STATUS']='V1026_NINJA %f/%t '
    start=time.monotonic()
    last=None
    def report():
        nonlocal last
        point=progress(log)
        # Do not guess progress when no Ninja status line is available.
        if point is not None and (last is None or point[0]>=last[0]):
            last=point
        elapsed=int(time.monotonic()-start)
        if last is None:
            print(f'V1026_LINK_PROGRESS elapsed_seconds={elapsed} completed=unknown total=unknown',flush=True)
        else:
            print(f'V1026_LINK_PROGRESS elapsed_seconds={elapsed} completed={last[0]} total={last[1]}',flush=True)
    # Preserve the original worker and timeout contract. Never emit stderr,
    # a compiler command, an original symbol, a generated path or raw output.
    with log.open('xb') as f:
        with subprocess.Popen(['timeout','--kill-after=10s','5100s','cmake','--build',str(build),
                               '--target','UndercoverWiiLocal','--parallel','2'],
                              env=env,stdout=f,stderr=subprocess.STDOUT) as proc:
            while True:
                try:
                    rc=proc.wait(timeout=30)
                    report()
                    return 0 if rc==0 else 1
                except subprocess.TimeoutExpired:
                    report()
def main():
    if len(sys.argv)!=2:return 2
    try:return run(Path(sys.argv[1]))
    except (OSError,ValueError,subprocess.SubprocessError):
        print('V1026_LINK_PROGRESS unavailable=1',flush=True);return 1
if __name__=='__main__':raise SystemExit(main())
