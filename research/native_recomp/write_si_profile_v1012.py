#!/usr/bin/env python3
"""Write one of two explicitly synthetic SI profiles; no guest memory edits."""
import argparse
from pathlib import Path

PROFILES = {
    "absent": ("absent", "absent", "absent", "absent"),
    "port1-present": ("absent", "090000", "absent", "absent"),
}

def render(profile):
    ports = PROFILES[profile]
    return "UNDERCOVER_SI_PROFILE_V1\nlatency=00000008\n" + "".join(
        f"port{i}={value}\n" for i, value in enumerate(ports)
    )

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("profile", choices=tuple(PROFILES))
    p.add_argument("output", type=Path)
    a = p.parse_args()
    # Exclusive creation preserves the clean per-launch workspace contract.
    with a.output.open("x", encoding="ascii", newline="\n") as f:
        f.write(render(a.profile))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
