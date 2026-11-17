#!/usr/bin/env python3
"""Fail-closed smoke check for V29 performance-SPR support after Wii V18/V20.

The existing V29 exact-source installer targets an upstream pre-HID layout.
After HID0/HID2 (V18) and L2CR (V20) rewrite nearby emitter branches, its
exact old-source anchors are intentionally no longer identical. Verify
the *installed* result instead of trying to patch again after V18/V20.

No game instructions, original binaries or generated owner code are used.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def require(data: str, needle: str, count: int, description: str) -> None:
    actual = data.count(needle)
    if actual != count:
        raise ValueError(f"missing or ambiguous source-only performance support: {description}")


def verify(root: Path) -> None:
    cpu=(root/"nWiiRuntime/include/runtime/cpu_context.h").read_text(encoding="utf-8")
    emitter=(root/"nWiiRecomp/src/recompiler.cpp").read_text(encoding="utf-8")
    ios=(root/"nWiiRuntime/src/hle/ios.cpp").read_text(encoding="utf-8")

    for field in ("mmcr0", "mmcr1"):
        require(cpu, f"uint32_t {field} = 0;", 2, f"{field} CPU/backup value")
    require(cpu, "std::array<uint32_t, 4> pmc{};", 2, "PMC CPU/backup array")

    for token in ("mfspr performance control", "mfspr performance counter",
                  "mtspr performance control", "mtspr performance counter"):
        require(emitter, token, 1, token)
    require(emitter,
            "ctx.mmcr0 = bk.mmcr0; ctx.mmcr1 = bk.mmcr1; ctx.pmc = bk.pmc;",
            2, "two dispatcher backup restore paths")
    require(ios,
            "bk.mmcr0 = ctx.mmcr0; bk.mmcr1 = ctx.mmcr1; bk.pmc = ctx.pmc;",
            2, "two IOS callback state-save paths")
    # V18/V20 must not have been accidentally reverted when V29 was installed.
    require(cpu, "uint32_t l2cr = 0;", 1, "Wii L2CR guest value")
    require(emitter, "mtspr HID0", 1, "HID0 state emission")
    require(emitter, "mtspr L2CR", 1, "L2CR state emission")


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("upstream",type=Path)
    args=ap.parse_args()
    verify(args.upstream)
    print("PASS: V29 performance SPRs coexist with V18 HID/V20 L2CR")

if __name__=="__main__":
    main()
