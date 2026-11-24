#!/usr/bin/env python3
"""Original-free compile gate for composed exact-root analyzer patches."""
import argparse,subprocess
from pathlib import Path
from apply_verified_elf_spans_v6 import apply as trusted
from apply_function_root_v443 import apply as root_identity
from apply_bat_roots_v586 import apply as bat
from apply_report_table_v594 import apply as report
from apply_stm_native_open_v632 import rewrite as stm
from apply_open_roots_v645 import apply as open_roots
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    root=a.root
    if subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()!='595f176f1d24cc54ff2e8389feed12d7fb553cc2':raise SystemExit(1)
    trusted(root);root_identity(root);bat(root);report(root,0x805204e8)
    f=root/'nWiiAnalyzer/src/analyzer.cpp';f.write_text(stm(f.read_text()))
    open_roots(root)
    subprocess.run(['g++','-std=c++20','-fsyntax-only','-I'+str(root/'nWiiRuntime/include'),'-I'+str(root/'nWiiAnalyzer/include'),str(f)],check=True)
    print('V647_OPEN_ANALYZER_COMPILE verified=1 original_free=1')
if __name__=='__main__':main()
