"""Read-only SHA-256 fingerprint tool for private local game extracts.

Does not parse, modify, or redistribute proprietary game assets.
"""
import argparse
import hashlib
from pathlib import Path

WII_REDBUILDING_SCENE_SHA256 = "cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--expected-sha256", default=None)
    args = parser.parse_args()
    result = sha256_file(args.path)
    print(f"SHA-256: {result}")
    if args.expected_sha256 and result.lower() != args.expected_sha256.lower():
        parser.error("SHA-256 mismatch; refusing to treat file as verified source")

if __name__ == "__main__":
    main()
