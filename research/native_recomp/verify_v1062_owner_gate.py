#!/usr/bin/env python3
"""Validate pinned public run metadata and private owner-job success."""
import json
import os
import re
import subprocess
from typing import NamedTuple

BRANCH = 'research/wii-native-recomp-preflight'


class Requirement(NamedTuple):
    run_id: int
    head: str
    path: str
    owner: str


REQUIREMENTS = (
    Requirement(45741527878, '65a7300bc1555e3e94e692132e9813671ee4e670',
                '.github/workflows/wii-v1029-third-transfer-preflight.yml', 'owner-execution'),
    Requirement(45740655991, '0b8dec7547f2245b37bd9d227b397a6ee0976812',
                '.github/workflows/wii-v1038-continuous-queue-history.yml', 'owner-execution'),
    Requirement(45742746303, '90b71ec01b245095278cb528a5d1be69c8753245',
                '.github/workflows/wii-v1007-second-rfi.yml', 'owner-context'),
    Requirement(45753506495, '5f1f83d179b770510cb5231ad5d13f90f1e656ae',
                '.github/workflows/wii-v1059-continuous-third-alarm.yml', 'owner-execution'),
    Requirement(45756409951, '0a4d51407909ae4e4f0f0e8b7e9f5823d21afcd6',
                '.github/workflows/wii-v1007-second-rfi.yml', 'owner-context'),
    Requirement(45757000670, 'cd1d4467e51f1ee962246e00b90b153d7640aa6c',
                '.github/workflows/wii-v1007-second-rfi.yml', 'owner-context'),
)


def verify(fetch, requirement):
    """Use the same successful attempt for the run and its job census."""
    run_path = f'actions/runs/{requirement.run_id}'
    run = fetch(run_path)
    if not isinstance(run, dict) or any(run.get(k) != v for k, v in (
        ('id', requirement.run_id), ('head_sha', requirement.head),
        ('head_branch', BRANCH), ('path', requirement.path),
        ('status', 'completed'), ('conclusion', 'success'),
    )):
        return False
    attempt = run.get('run_attempt')
    if type(attempt) is not int or attempt < 1:
        return False
    census = fetch(f'{run_path}/attempts/{attempt}/jobs?per_page=100')
    if not isinstance(census, dict):
        return False
    jobs = census.get('jobs')
    if (not isinstance(jobs, list) or type(census.get('total_count')) is not int
            or census['total_count'] != len(jobs) or not 1 <= len(jobs) <= 100
            or any(not isinstance(job, dict) for job in jobs)):
        return False
    owner = [job for job in jobs if job.get('name') == requirement.owner]
    return (len(owner) == 1 and owner[0].get('run_id') == requirement.run_id
            and owner[0].get('status') == 'completed'
            and owner[0].get('conclusion') == 'success')


def main():
    repo = os.environ.get('GH_REPO', '')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        print('V1062_OWNER_GATE verified=0 reason=repository')
        return 1

    def fetch(path):
        output = subprocess.run(['gh', 'api', f'repos/{repo}/{path}'], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=30).stdout
        if len(output) > 2 * 1024 * 1024:
            raise ValueError('metadata size')
        return json.loads(output)

    for index, requirement in enumerate(REQUIREMENTS, 1):
        try:
            if not verify(fetch, requirement):
                print(f'V1062_OWNER_GATE verified=0 gate={index} reason=metadata')
                return 1
        except (OSError, ValueError, subprocess.SubprocessError):
            print(f'V1062_OWNER_GATE verified=0 gate={index} reason=unavailable')
            return 1
    print('V1116_PREREQUISITES verified=1 historical_installer=1 queue=1 focused_alarm=1 continuous_alarm=1 focused_wireless=1 focused_setter=1')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
