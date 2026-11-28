# Windows native whole-image post-system-time boundary

## Why this exists

The original Wii DOL/ELF already produced a linked and launched complete
Windows x64 PE in the V426 owner lane. The V709 Windows SI/OS-leaf boundary
was separately authenticated. The Linux native V742 continuation verified
the actual 25-word repeated `__OSGetSystemTime` route and exited at its
caller return. The Windows `os-si-handler-time` lane now installs that
same source-only authenticated route, but **a Windows V742 owner success
must be observed separately** and must not be inferred from Linux.

The post-time V747 production observer already allows a bounded suffix
without emulating the next linked dependency. A new Windows **opt-in**
executes that exact observer on the complete native PE and requires a
refusal *before* entering the first unsupported linked call.

## Build and verification

Main workflow:
[Wii Native Windows Complete Image](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/workflows/wii-native-windows-full.yml)

Dedicated original-free and owner-private lane:
[Wii V750 Windows Original Post-Time Boundary](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/workflows/wii-v750-windows-time-suffix.yml)

The new switch is `--owner-time-suffix` in
`windows_full_build_v426.py`. It is only valid for a SHA-pinned owner
DOL/ELF using `--owner-scope os-si-handler-time`; it is rejected for
synthetic or unrelated scopes. Without the switch, the existing owner
V742 and synthetic smoke tests are unchanged.

Example, on a private Windows host with pinned upstream translator and
original game inputs in private paths:

```powershell
python research/native_recomp/windows_full_build_v426.py <pinned-NWiiRecomp-root> <empty-private-build-path> --owner-dol <private-Wii-DOL> --owner-elf <private-Wii-ELF> --owner-scope os-si-handler-time --owner-time-suffix
```

With the opt-in flag, the generated original-code execution must produce
the V742 return and then terminate with exit code 126 only when the V747
control, next-call refusal, and error witness match all three independent
bounded records. The verifier checks the unmodified V742 prefix with the
original Windows scope auditor, then separately validates the V747 suffix.
It rejects missing/duplicate events, forged early suffix events, unrelated
runtime failures, contradictory call ordinals, guest-code entry beyond the
guard, Windows exceptions, and process timeouts.

Success would print:

```text
V750_WINDOWS_SUFFIX exit=expected_refusal time_verified=1 boundary_verified=1 handler_return=0 boot_verified=0
```

The Windows executable is built with pinned MSVC x64, checks its PE
entry, and runs an actual original game-code path. The private DOL, ELF,
translated C++, binaries, unfiltered traces and runtime logs remain
owner-private and are deleted from the ephemeral runner.

## Validation and limits

Original-free regression:

```sh
python3 -m unittest discover -s research/native_recomp -p test_v750_windows_time_suffix.py -v
```

It exercises the option refusal matrix and exact redacted-log evidence,
including malicious or mismatched markers and a Windows NTSTATUS value.
The dedicated workflow separately tests the existing V747 audit and
V429 scope controls before allowing the private build.

This milestone is **not** an original Windows V747 success unless an
owner-private workflow has finished with the exact positive audit line.
It is not the whole SI handler return, RFI return, original `main`,
first frame, frontend, or playable PC port. The next step is to
authenticate the newly reached callsite or follow a taken path away from
it without inventing guest behavior.

Note: the `V750_WINDOWS_SUFFIX` name describes the Windows diagnostic
lane and is independent of the existing V750 SI follow-on witness.
