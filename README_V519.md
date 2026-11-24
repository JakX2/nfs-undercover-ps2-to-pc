# V519: native SI device scheduling and Windows EXI polling

## Authenticated original execution

* V509 Windows complete-image owner run [45340319188](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340319188): original DOL/ELF verified, Windows x64 linked, V491 EXI polling witness 2/2, fallback=0, verified=1. This is not full OSInit or a game boot.
* V508 NAND replay [45340216490](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340216490): historical ACK and successor authenticated, 44 calls, 25 unique original entries, resumed=1, history=1, final_clear=0; new known public guard ID 1237, rc=134. Workflow completion means the bounded audit worked, not that NAND initialization completed.
* Linux V507 EXI ID owner [45340033230](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340033230) and V513 absent-card owner [45340918843](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340918843) remained outstanding at the last check.

## New changes

| Version | Change | Verification |
| --- | --- | --- |
| V514 | Explicit present/absent SI type endpoints; native instruction deadline, token isolation, four ports, strict unknown-command rejection | [ASan/UBSan and pinned runtime regression passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45341929726) |
| V515 | Reversible emitter/context hook after V497, optional SI tick binding | [Actual pinned generated PPC in split and non-split modes passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342005651); no interpreter |
| V516 | Windows next scope os-exi-handlers | [Owner build queued/running](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342083001) |
| V517 | Correlate successor failure with public source only; no guard changes | [Original-free tests passed; owner replay running](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342147666) |
| V518 | Strict explicit SI profile parser and opt-in host session | [Candidate CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342249671) |
| V519 | Validate that SI session and active MMIO refer to the same controller; pinned-header test | Candidate; requires CI |

## SI profile contract

Explicit test-only profile file, with a final newline and all ports specified. Example:

```
UNDERCOVER_SI_PROFILE_V1
latency=00000008
port0=123456
port1=absent
port2=abcdef
port3=absent
```

Type bytes are synthetic examples, not a claimed physical controller ID. Latency is native instruction visits, not Broadway clock cycles. Only command 0 with one outgoing and three incoming bytes is supported. An absent port explicitly completes with NOREP and does not overwrite communication RAM. Unsupported commands fail closed. Polling never completes requests. Runtime wiring is opt-in; a profile requires UNDERCOVER_V512_SI=1 and UNDERCOVER_V518_SI_PROFILE set to a valid private file.

## Next boundary

Wait for the independent authenticated EXI ID and absent-card scopes to finish before extending the complete-image startup into SI. Retain original guest IRQ registration, EXI version routine return, SI initialization and actual guest command/queue behavior. The native SI model does not yet implement controller polling, VI timing, callbacks, or live input. No owner original SI execution or full game boot is claimed. Do not publish original code, raw private logs, assets or executables.
