# V17: Carbon PC external loader A/B/A capture calibration

Date: 2026-11-12. Source-only offline validation using owner-private
Carbon PC files and ProcMon CSV exports. No installed game is modified
or executed by this tool. No original licensed resources are published.

## Why A/B/A?

The V15–V16 source checks connect one XNFSModFiles.txt manifest, one
structurally complete native Carbon PC BUN chunk stream and one ProcMon
capture of NFSC.exe disk access. However a single positive file read
could be unrelated to the loader toggle, and an empty capture may simply
mean ProcMon filtering was misconfigured.

V17 adds a **three-run A/B/A evidence comparison** using:

- A1: clean Carbon baseline, external-loader control disabled.
- B: one known-good ORIGINAL Carbon PC external resource enabled.
- A2: restore the clean baseline, external-loader control disabled.
- Stock calibration: a separate, known original Carbon .BUN or .BIN
  file normally read by NFSC.exe must show a successful CreateFile
  followed by ReadFile under the same PID in ALL THREE captures.

This last requirement is a **capture quality check**, not proof that
the whole game launched normally or that all file operations were logged.

## New source-only code

- carbon_pc_external_aba_capture_gate.py supplies pure
  audit_carbon_external_aba(manifest_bytes, original_resource_bytes,
  baseline_csv, control_csv, restore_csv, windows_game_root,
  windows_external_path, windows_sentinel_path, kind).
- It reuses the previously tested V16 complete-file resource parser
  and V15 manifest-to-file binding.
- Each phase's ProcMon CSV is read separately with an independent,
  bounded exact-path NFSC.exe same-PID CreateFile then ReadFile
  calibration check against the stock sentinel.
- A positive external-file read is reported as **isolated to control**
  only if all three captures were calibrated, neither baseline nor
  restore contains a successful target-file CreateFile/ReadFile, and
  control has a successful exact target open/read in a PID that also
  calibrated its ordinary stock-file access.
- Full-file byte coverage in control is determined by the existing
  bounded union-of-offsets calculation; it is NOT necessary to call
  that full read "asset registration." Original hash/filename/PID
  values remain private and are not returned.

The owner-local audit_owner_aba_files CLI also validates game-folder
containment, one unambiguous XNFSModFiles manifest, independent
source/config/capture paths and no symlinks or changed files.
A stock game sentinel may be up to 2 GiB and is **stat-checked only**,
not read into RAM. The external control file still has the strict
32 MiB source-inspection bound.

## Read-only Windows command

The following paths are purely illustrative. Keep every game file
and ProcMon CSV in private owner-local storage.

    python research/world_bridge/carbon_pc_external_aba_capture_gate.py --carbon-game-dir "C:\Carbon-Test" --xnfs-manifest "C:\Carbon-Test\scripts\XNFSModFiles.txt" --original-carbon-bun "C:\Carbon-Test\MODS\KnownGoodPC.BUN" --stock-sentinel-bun "C:\Carbon-Test\TRACKS\STREAML5RB.BUN" --kind geometry --baseline-csv "C:\Private\carbon-baseline.csv" --control-csv "C:\Private\carbon-control.csv" --restore-csv "C:\Private\carbon-restored.csv"

ProcMon exports must include Process Name, PID, Operation, Path,
Result and Detail columns; begin capture before launching NFSC.exe.
Select a stock .BUN or .BIN actually opened and read on every launch.
Do not use the external MODS file as the sentinel. Save the original
three CSV exports privately, do not share local paths/IDs.

If using the public third-party XNFSModFiles loader, explicitly
control whether the loader is enabled in each run using a clean,
backed-up test setup. The V17 tool **cannot independently verify**
that the ASI was absent on A1/A2 or present on B: it only compares
the user-supplied traces. The final audit is performed when the
restored Carbon test folder is back in the verified control layout
with the single manifest and private original resource available
for read-only validation. No CLI step here copies or installs the
manifest/resource or turns the loader on/off.

## Evidence classification

- ISOLATED_EXTERNAL_FILE_READ_OBSERVED_NOT_REGISTRATION:
  positive three-run calibrated ProcMon difference, with a
  same-PID control external file read and stock sentinel read.
  Full file read is reported independently as a boolean.
- INCONCLUSIVE_CAPTURE_CALIBRATION_MISSING:
  one or more captures lacks a successful stock-file open/read.
- INCONCLUSIVE_EXTERNAL_TARGET_NOT_ISOLATED_TO_CONTROL:
  baseline or restore saw positive matching external-file I/O.
- INCONCLUSIVE_CONTROL_TARGET_ACCESS_WITHOUT_CALIBRATED_READ:
  target file access occurred, but it was not a matching
  same-PID ordered read with a calibrated stock-file read.
- INCONCLUSIVE_NO_CONTROL_FILE_READ:
  none of the above produced positive target I/O.

**None** confirms that the third-party ASI ran, called
CreateResourceFile or BeginLoading, registered game geometry, sampled
textures, changed visual output or loaded an Undercover PS2/Wii asset.

## Tests and next experiment

test_carbon_pc_external_aba_capture_gate.py uses synthetic Carbon
geometry, texture chunks, fake Windows paths and ProcMon CSVs.
It covers a full file, a composite chunk stream, all three
calibration failures, file reads in baseline/restore, wrong PID,
file-open-only, no target access, original source mismatch,
invalid manifests/paths/CSV, privacy, symlinks, duplicate captures,
shadowed manifests and a sparse >32 MiB stock calibration file.

Run the original-free suite:

    PYTHONPATH=research/world_bridge python -m unittest discover -s research/world_bridge -p 'test_*.py' -v

The GitHub Actions source-only workflow runs without original
game assets or third-party binaries.

Next is a genuine **owner-local Windows** A/B/A session using
one *known-good original Carbon PC external loader bundle* with
verified loader packaging. If it shows isolated disk access, still
seek independent loader API/registration and visual baseline/control/
restore evidence. Only then apply the proven route to one converted
Undercover scenery model and its textures.

The Carbon PC conversion PR #33 remains draft. Separate Wii-to-native
C++ physics research PR #35 is unchanged. The game is NOT playable
through this pipeline yet.
