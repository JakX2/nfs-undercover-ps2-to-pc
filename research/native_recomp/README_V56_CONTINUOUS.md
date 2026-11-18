# V56: continuous native uncached EXIGetID
Verified with the SHA-pinned owner DOL in GitHub Actions run [44205185734](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44205185734), commit b44d4005335ee8301cfe52c29c75574f882351e7.

Starts at original `__start` (0x8000403C) and stops at 0x804EFAB4, after the original channel-0/device-2 ID request has returned. All 16 trials complete original lock/select, two immediate transfers, sync, deselect, and inline unlock; ID recovered from the synthetic hardware data register through original PPC instructions. No RAM ID injection, interpreter fallback, or null-indirect-callback bypass. Busy timing independently varied from zero to three polls on both transfers, with strict state/width/order checks. Alternate console-type, card-present, and queued-callback paths remain explicit test stops. The MMIO device is a narrow test oracle, not a complete EXI implementation or a native Windows game boot.

Run privately with `run_v56_continuous_exi_transaction.sh NWII_ROOT OWNER_DOL` after preparing the same pinned, patched NWii runtime as V55. Original executable bytes and translated game source are never published.
