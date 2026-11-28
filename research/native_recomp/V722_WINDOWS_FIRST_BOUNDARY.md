# V722: Windows complete-image first-boundary diagnostics

## Verified baseline

The complete native Windows build path already existed before V722. In
[owner run 45530252603](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45530252603),
the pinned NWiiRecomp translated the SHA-authenticated Wii DOL/ELF, compiled
and linked `UndercoverWiiLocal.exe` with MSVC x64, validated its PE entry,
launched it on Windows, and reported
`V426_WINDOWS_LINK linked=1 platform=windows-x64 synthetic=0 boot_verified=0`.
Its bounded original SI dispatcher passed all six stages:
`V667_SI_DISPATCH_CENSUS rc=0 external=1 stages=6 verified=1 boot_verified=0`.

This was **not a full game boot**. Do not equate the separate
127-instruction formatter witness with the complete-image startup route.
The newer `os-si-os-leaves` route is a distinct, gated continuation.

## What V722 changes

`windows_full_build_v426.py` now records whether its 20-second native
launch actually expired. The OS can legitimately return exit code 124;
previously a host timeout was represented by the same number. The new
`timeout_status` output separates these outcomes without altering the
existing subprocess return-code interface used by the build stages.

For `os-si-os-leaves` only, `windows_boot_frontier_v722.py` consumes
the existing redacted V709 audit markers and prints one bounded summary:

```text
V722_WINDOWS_FRONTIER scope=os-si-os-leaves exit=<class> last=<checkpoint> next=<checkpoint> reason=<class> scope_verified=<0|1> boot_verified=0
```

All fields are from fixed enumerations. No original instruction words,
addresses, register contents, generated source, or arbitrary guest log
lines are printed. The summary distinguishes an absent/duplicate ACK,
the first missing ordered post-ACK checkpoint, unexpected event ordering,
numbered loop-poll failures, trailing events, nonzero process exits,
Windows exceptions, and timeouts. Its last-seen checkpoint is a **debug
observation**, not proof of correct guest execution. Only the pre-existing
full V709 audit may set `scope_verified=1`; a timeout cannot do so.

The existing 8 MiB owner-launch-log cap, PE verification, strict DOL/ELF
provenance, source guards, and private workspace cleanup are unchanged.

## Reproduction and acceptance

Workflow: [Wii Native Windows Complete Image](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/workflows/wii-native-windows-full.yml).
Use `research/wii-native-recomp-preflight`, the default
`owner_scope=os-si-os-leaves`, and both legacy controls disabled.
The Windows synthetic job first runs
`test_v722_windows_boot_frontier.py`, followed by the pinned translator,
native compile, PE validation and an independently written synthetic PPC
program launch. Only after the synthetic job succeeds and owner-private
authorization is available may the private owner job translate, link and
execute the SHA-pinned original image.

To exercise just the original-free diagnostic tests on any host:

```sh
python3 -m unittest discover -s research/native_recomp -p test_v722_windows_boot_frontier.py -v
```

The test includes a real host subprocess returning 124 and a separately
timed-out subprocess, all ordered startup checkpoints, missing/duplicate
ACK, unexpected/forged markers, invalid loop polls, nonzero/NTSTATUS exit,
private-log redaction and rejection of an invalid success claim.

## Next original-runtime blocker

Use the owner-private Windows log's `V709_OS_LEAF_CENSUS` together with
`V722_WINDOWS_FRONTIER` to identify the first unobserved post-ACK
checkpoint. Reproduce the same boundary with the current Linux
complete-image runner and the original-free synthetic fixtures. Fix the
specific Wii runtime, scheduling or AOT emission defect, re-run the
Windows owner scope, and only then promote its verified frontier.

The V722 change itself is a diagnostic and timeout-accounting improvement,
**not an additional original instruction, first frame or gameplay claim**.
