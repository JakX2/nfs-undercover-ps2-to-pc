#!/usr/bin/env python3
"""Install the real native zero helper in a generated fixture runtime.
The fixture translates only DCFlushRange/vector; zero events invoke the
actual flat-RAM method, not a translated DCZeroRange body.
"""
import argparse
from pathlib import Path
from prepare_v419_full_start import replace_exact
from apply_dcbz_v67 import CONTEXT,HEADER,OLD_INCLUDE,NEW_INCLUDE,OLD_CTX,NEW_CTX
from apply_arena_cache_trace_v596 import apply
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    host=Path(__file__).parent
    try:
        cp=a.root/CONTEXT;hp=a.root/HEADER
        if cp.is_symlink() or hp.exists() or hp.is_symlink():raise ValueError('destination')
        source=replace_exact(replace_exact(cp.read_text(encoding='utf-8'),OLD_INCLUDE,NEW_INCLUDE),OLD_CTX,NEW_CTX)
        hp.write_bytes((host/HEADER.name).read_bytes());cp.write_text(source,encoding='utf-8')
        apply(a.root,host)
    except (OSError,ValueError,UnicodeError):print('V598_ARENA_FIXTURE installed=0');return 1
    print('V598_ARENA_FIXTURE installed=1');return 0
if __name__=='__main__':raise SystemExit(main())
