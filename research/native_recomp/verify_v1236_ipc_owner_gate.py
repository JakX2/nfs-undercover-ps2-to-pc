#!/usr/bin/env python3
"""Gate the next private build on the exact existing owner runs, never rerun them."""
import argparse
import json
import os
import re
import subprocess
import time
from verify_v1062_owner_gate import BRANCH, Requirement, verify

REQUIREMENTS = (
    Requirement(45779697920, '78d040de355c6059a28dab56cd4983ebeed689ae',
                '.github/workflows/wii-v1059-continuous-third-alarm.yml', 'owner-execution'),
    Requirement(45781285404, '748cb05e4ebc808bc6148133c37198195aba3c37',
                '.github/workflows/wii-v1232-post-ack-ipc-preflight.yml', 'owner-execution'),
    Requirement(45782480660, '025d9df86b74b0b2302782249e9e6b482c945ead',
                '.github/workflows/wii-v958-second-ack-integration.yml', 'original-free'),
)
PENDING = {'queued', 'in_progress', 'waiting', 'pending', 'requested'}

def classify(fetch, req):
    path = f'actions/runs/{req.run_id}'
    run = fetch(path)
    if not isinstance(run, dict) or any(run.get(k) != v for k, v in (
        ('id', req.run_id), ('head_sha', req.head), ('head_branch', BRANCH), ('path', req.path),
    )):
        return 'refused'
    if type(run.get('run_attempt')) is not int or run['run_attempt'] != 1:
        return 'refused'
    if run.get('status') in PENDING and run.get('conclusion') is None:
        return 'pending'
    if run.get('status') != 'completed' or run.get('conclusion') != 'success':
        return 'refused'
    # Verify against the same immutable metadata response and pinned attempt.
    return 'verified' if verify(lambda p: run if p == path else fetch(p), req) else 'refused'

def check(fetch):
    return tuple(classify(fetch, req) for req in REQUIREMENTS)

def gate(fetch, wait=False, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + 40 * 60
    while True:
        states = check(fetch)
        print('V1236_OWNER_GATE callback='+states[0]+' ipc_preflight='+states[1]+' integration='+states[2], flush=True)
        if 'refused' in states:
            return 1
        if states == ('verified',)*len(REQUIREMENTS):
            return 0
        if not wait or clock() >= deadline:
            return 1
        sleep(min(60, max(0, deadline-clock())))

def main():
    p=argparse.ArgumentParser();p.add_argument('--wait',action='store_true');a=p.parse_args()
    repo=os.environ.get('GH_REPO','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        print('V1236_OWNER_GATE refused=repository');return 1
    def fetch(path):
        raw=subprocess.run(['gh','api',f'repos/{repo}/{path}'],check=True,stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL,timeout=30).stdout
        if len(raw)>2*1024*1024:raise ValueError('metadata size')
        return json.loads(raw)
    try:return gate(fetch,a.wait)
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        print('V1236_OWNER_GATE refused=metadata');return 1
if __name__=='__main__':raise SystemExit(main())
