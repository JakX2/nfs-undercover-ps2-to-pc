"""Local-only validation; never writes to an installed game."""
import argparse
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-fixtures', action='store_true', help='Run fixture-dependent regression tests if local game inputs exist')
    args = parser.parse_args()
    sources = sorted((ROOT / 'research').rglob('*.py'))
    if not sources:
        parser.error('No Python sources found')
    for src in sources:
        py_compile.compile(str(src), doraise=True)
    print(f'PASS: Python syntax for {len(sources)} source files')
    if not args.with_fixtures:
        print('Fixture-backed regression tests intentionally not run; pass --with-fixtures after supplying local input files.')
        return 0
    for version, modules in [('v41', ['test_v41']), ('v46', ['test_v46','test_v45','test_v44','test_v43'])]:
        cmd=[sys.executable,'-m','unittest',*modules,'-q']
        print(f'Running {version} fixture-backed suite...', flush=True)
        subprocess.run(cmd, check=True, cwd=ROOT/'research'/version)
    return 0

if __name__=='__main__':
    sys.exit(main())
