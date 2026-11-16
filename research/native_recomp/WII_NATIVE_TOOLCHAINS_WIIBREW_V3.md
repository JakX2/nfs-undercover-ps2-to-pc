# V3: native Wii recompilation toolchains and WiiBrew reference gates

Research date: 2026-11-13. Source-only; NOT a native game boot or completed PowerPC translation.

## Owner-connected archives
Wiicompiled-0.9.4.zip provides generic DOL translator/manifest support. NWiiRecomp-master.zip provides analyzer, symbol CSV importer, PPC generator and Wii HLE runtime. dolphin-master.zip is a hardware oracle. aurora-main.zip is a GX/PAD/DVD/CARD compatibility candidate; dawn-main.zip is its WebGPU engine dependency. yet_another_gamecube_doc.zip contains hardware details. GhidraRPXLoader-master.zip is for Wii U RPX/RPL, not this Wii DOL.

## Original-source results
V3's owner-local symbol bridge successfully generated 27,941 unique function-address rows from matching, private Undercover Wii ELF/DOL, and a project TOML accepted by Python's TOML parser. Six new synthetic-only adapter tests passed, as did five V1 preflight tests. No console game files or generated symbol CSV are distributed.

## Upstream source contract
The shipped NWiiRecomp source parses project_name, input_game_dir, output_dir, runtime_source_dir, symbols_csv, split_output and instructions_per_file from TOML. Executable::load_unpacked_game accepts a direct DOL path for analysis; full runtime operation additionally requires game data and Wii boot services. Its symbol importer accepts CSV rows Name,Location,Size, with hex locations and simple comma-separated parsing. The V3 bridge uses unique, sanitized, address-prefixed names.

## WiiBrew gates
- MEM1: cached 0x80000000..0x817FFFFF (24 MiB), uncached alias 0xC0000000..0xC17FFFFF.
- MEM2: cached 0x90000000..0x93FFFFFF (64 MiB), uncached alias 0xD0000000..0xD3FFFFFF. Some top MEM2 is reserved by IOS.
- OS low memory contains RAM sizing, FST pointers and arena values, plus IOS IPC buffer pointers.
- IOS calls use a 0x40-byte request structure and Hollywood IPC control; honor MMIO registers and async acknowledgments.
- GX CPU FIFO uses 0xCC008000 WGPIPE and CP/XF/BP state commands.

Sources:
https://wiibrew.org/wiki/Memory_map
https://wiibrew.org/wiki/Hardware/IPC
https://wiibrew.org/wiki/IOS
https://wiibrew.org/wiki/Hardware/GX
https://wiibrew.org/wiki/Hollywood/Registers

## Limitations and next steps
The local host has neither .NET SDK nor NWiiRecomp's required SDL2/tomlplusplus dependencies. Thus no upstream translation or headless native game boot has been run. Build toolchains in an appropriate host environment, log unsupported PowerPC instructions, then compare OSInit and main checkpoints against Dolphin. The generic WiiCompiled preflight manifest's 24 MiB MEM1 declaration must not be mistaken for the full Wii runtime mapping; MEM2/aliases/IOS need separate treatment.

All original game assets, full private symbol maps, private project TOMLs, and generated game code remain owner-local.
