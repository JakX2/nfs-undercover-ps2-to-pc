# V14: Carbon PC known-good external resource read control

**2026-11-11.** Owner-local read-only source-only evidence. No original game
binaries, copyrighted assets or third-party injection DLL distributed here.

## Why this control exists

The existing PC-shaped Undercover eSolid/DXT5 converter, native PC header
normalizer, and V13 resource namespace check cannot prove that the **running**
Carbon PC game loader opens, registers, or renders newly added data.

Our next milestone is a controlled, reversible experiment with a
**known-good ORIGINAL Carbon PC resource**. Only once such a control works
should a converted Undercover resource be introduced.

The public [XNFSModFiles project](https://github.com/xan1242/xnfsmodfiles)
lists Carbon as supported and describes it as a chunk resource
adder/replacer. Its
[Carbon_addresses.h](https://github.com/xan1242/xnfsmodfiles/blob/master/XNFSModFiles/Carbon_addresses.h)
identifies CreateResourceFile 0x006B32C0, BeginLoading 0x006B5910,
preinit cave 0x006B6D56 and postinit cave 0x006B7850, the same
addresses checked by our read-only PE ABI preflight.

More importantly, its actual
[dllmain.cpp](https://github.com/xan1242/xnfsmodfiles/blob/master/XNFSModFiles/dllmain.cpp)
reads **XNFSModFiles.txt**, first in the process working directory,
then in scripts/XNFSModFiles.txt. The bundled
[example](https://github.com/xan1242/xnfsmodfiles/blob/master/XNFSModFiles%20-%20Example.txt)
provides the stage,type,relative-filename pattern with values 0,1;
1,1; and 1,6. Stage 0 is preinit and stage 1 is postinit. The public
README mentions an .ini, but the actual source uses XNFSModFiles.txt.

The original third-party C parser relies on fixed-size lines and sscanf;
our manifest gate deliberately accepts only one unambiguous safe entry.

## Two new source-only tools

### A. Read-only manifest validator

File: carbon_pc_xnfsmodfiles_manifest_gate.py

- Parses exactly ONE original-format XNFSModFiles.txt record,
  with stage 0 or 1, type 1 or 6, relative MODS/*.BUN path.
- Rejects unknown stages/types, duplicate/extra loader entries,
  path traversal, absolute paths, whitespace ambiguities, oversized
  buffers, inline comments, malformed CRLF, symlinks and changed files.
- Returns an identity-free metadata report with all runtime loader claims
  explicitly FALSE. It NEVER installs or executes the public ASI.

Example synthetic manifest line:

    1,1,MODS\KnownGoodPC.BUN

This is only a SOURCE FORMAT control. A correct manifest does not mean
any arbitrary raw PC resource root is a loader-compatible bundle, nor
that resource type 1 is universally correct for novel scenery.

### B. Exact-file ProcMon read evidence

File: carbon_pc_external_resource_read_gate.py

- Accepts a bounded owner-original Carbon PC geometry root or PC
  texture root and validates native PC framing with existing strict
  binary format readers.
- Reads an owner-private ProcMon CSV; requires the same NFSC.exe process
  PID to have a SUCCESS CreateFile followed by SUCCESS ReadFile on
  the **exact normalized external path**, not a suffix match.
- Validates read offsets/lengths and returns unique covered bytes for
  ONE process; overlapping reads or different PIDs cannot combine.
- Evidence status distinguishes full file read, partial read, open/read
  without verified offsets, open-only and no captured positive access.
- Reports no private resource IDs, names, source paths, PIDs or data bytes.

A positive file read demonstrates disk access, NOT successful game
resource registration, loader ABI, model drawing, material sampling
or an Undercover world port. Missing ProcMon events may reflect
filtering, caching or memory-mapped I/O; absence is inconclusive.

## Controlled owner-local Windows procedure

1. Work with a **clean, backed-up copy of Carbon PC**. Verify that
   NFSC.exe starts normally and separately check its original PE
   code addresses with carbon_pc_external_loader_abi_preflight.py.
2. If desired, install the **correct Carbon build** of XNFSModFiles
   following its public project instructions in the test copy only.
   No tool here installs or modifies the game's executable/ASI.
3. Place one known-good original Carbon PC bundle in the private MODS
   directory in a layout that the public third-party loader actually
   accepts. Keep an untouched reference copy. Prepare a one-entry
   XNFSModFiles.txt; avoid a working-directory copy shadowing the
   scripts version.
4. From the research repository root, run this read-only validator
   (paths below are fictional owner-local examples):

    python research/world_bridge/carbon_pc_xnfsmodfiles_manifest_gate.py --xnfs-manifest "C:\Carbon-Test\scripts\XNFSModFiles.txt" --expected-control-relative-path "MODS\KnownGoodPC.BUN"

5. Capture NFSC.exe file I/O using ProcMon, including Process Name,
   PID, Operation, Path, Result and Detail, starting BEFORE game launch.
   Save the CSV privately. Close the game.
6. Run the independent read-only source-root and CSV audit:

    python research/world_bridge/carbon_pc_external_resource_read_gate.py --native-carbon-root "C:\Carbon-Test\MODS\KnownGoodPC.BUN" --kind geometry --procmon-csv "C:\Private\carbon-external-control.csv"

   Choose --kind texture for an original PC texture root. **The
   supplied file must be a complete extracted native PC geometry or
   texture root** for this strict reader; some third-party-loader-valid
   .BUN wrappers may instead require a separate unpacking step.
7. If ProcMon confirms exact-file access, verify actual registered
   resource and visible change **separately**, with baseline/test/restore
   observations. Existing private screenshot and session gates may help
   but cannot prove registration from a screenshot alone.
8. Only after the original Carbon control is validated, try ONE
   converted Undercover model with all its textures on a known loader
   path. Use the V13 namespace gate to detect identity conflicts.

This documented process is NOT a claim that the Carbon external loader,
the original Carbon control, or an Undercover candidate has already
been successfully run.

## Synthetic CI verification

    PYTHONPATH=research/world_bridge python -m unittest discover -s research/world_bridge -p 'test_*.py' -v

Tests cover correct native resource root parsing; exact filename;
successful ordered file I/O; no combining read ranges from separate
processes; malformed, clipped and duplicate reads; redacted output;
Windows CRLF loader manifest; safe stage/type/path; rejects extra
entries, traversal, ambiguity and invalid original file inputs.

No private assets, external loader executables, or original game process
are required by the source-only CI.

## Remaining gates

- Verified Carbon external loader installation and correct ABI: NO.
- An owner-original Carbon test resource loaded/registered at runtime: NO.
- Undercover PS2/Wii scenery correctly rendered in Carbon PC: NO.
- Playable Undercover on Carbon PC: NO.

Keep this separate research in draft PR #33; Wii-to-native C++ physics
remains independently developed in draft PR #35.
