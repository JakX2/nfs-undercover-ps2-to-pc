#!/usr/bin/env python3
"""Patch upstream NWiiRuntime's DOL loader with a checked, atomic parser.

No original Undercover files, generated game code, or proprietary assets.
"""
import argparse
from pathlib import Path

TARGET = Path('nWiiRuntime/src/core/loader.cpp')
HEADER = Path('nWiiRuntime/include/loader/validated_dol_v12.h')
START = 'bool Executable::load_dol(const std::string& path) {'
END = '\nbool Executable::load_rel('

REPLACEMENT = '''bool Executable::load_dol(const std::string& path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) {
        std::cerr << "[DOL] Unable to open: " << path << "\\n";
        return false;
    }
    const std::streamoff length = file.tellg();
    if (length < 0x100 || length > 128 * 1024 * 1024) {
        std::cerr << "[DOL] Invalid file size\\n";
        return false;
    }
    file.seekg(0);
    std::vector<uint8_t> bytes(static_cast<size_t>(length));
    if (!file.read(reinterpret_cast<char*>(bytes.data()), length)) {
        std::cerr << "[DOL] Short read\\n";
        return false;
    }
    ValidatedDolV12 parsed;
    std::string error;
    if (!parse_validated_dol_v12(bytes, parsed, error)) {
        std::cerr << "[DOL] " << error << "\\n";
        return false;
    }
    std::vector<Section> loaded;
    loaded.reserve(parsed.sections.size());
    for (const auto& part : parsed.sections) {
        Section sec;
        sec.address = part.guest_address;
        sec.size = part.size;
        sec.is_text = part.executable;
        sec.is_bss = part.is_bss;
        if (!part.is_bss) {
            sec.data.assign(bytes.begin() + part.file_offset,
                            bytes.begin() + part.file_offset + part.size);
        }
        loaded.push_back(std::move(sec));
    }
    // Commit atomically after every section and range is validated.
    sections = std::move(loaded);
    entry_point = parsed.entry_point;
    return true;
}
'''


def apply(root: Path, src: Path) -> bool:
    target = root / TARGET
    header = root / HEADER
    content = target.read_text(encoding='utf-8')
    if header.exists() and header.read_bytes() != src.read_bytes():
        raise ValueError('conflicting validated DOL header')
    if REPLACEMENT in content:
        if '#include "loader/validated_dol_v12.h"' not in content:
            raise ValueError('patch body present without include')
        return False
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError('unrecognized DOL loader source')
    a = content.index(START)
    b = content.index(END, a)
    if 'return load_dol(dol_path);' not in content[b:]:
        raise ValueError('unexpected NWiiRuntime loader version')
    # Validate target layout before any write.
    next_content = content[:a] + REPLACEMENT + content[b:]
    next_content = '#include "loader/validated_dol_v12.h"\n' + next_content
    if not header.exists():
        header.write_bytes(src.read_bytes())
    target.write_text(next_content, encoding='utf-8')
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream_root', type=Path)
    ap.add_argument('--header', type=Path, default=Path(__file__).with_name('validated_dol_v12.h'))
    args = ap.parse_args()
    print('Applied V12 validated DOL loader patch:', apply(args.upstream_root, args.header))
