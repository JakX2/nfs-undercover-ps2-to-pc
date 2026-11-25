# V925: verified native IRQ epilogue evidence

## Continuous original startup: V919

Owner workflow [45603607708](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45603607708), job 139168779197, commit 3f4bb7ce107197672372edb81fb3363f74d21986: success. Complete image configured, built, verified, linked and executed. Original SI handler ordinal 12 called its original restore routine; 16 visits, 15 GPRs restored, ABI checks passed. Stop occurs at the original final BLR boundary, before the handler return. This is the latest verified continuous startup milestone at time of writing.

## Focused original-code composition: V923

Owner workflow [45606067294](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45606067294), job 139177483884, commit aac1ffc4b2a90fc56d8fef2cf578d66631595475: success.

| Native build | Valid | Switch refusal | Corrupt saved context refusal | Corrupt saved GPR refusal |
| --- | ---: | ---: | ---: | ---: |
| Nonsplit | 8 | 1 | 1 | 1 |
| Split | 8 | 1 | 1 | 1 |

Both builds cover 113 original labels and six verified direct edges. All 16 valid cases executed original handler return, original dispatcher, scheduler enable, reschedule, 54-instruction context loader, native RFI and synthetic resume instruction with zero interpreter fallbacks. Six invalid cases rejected. ASan/UBSan-enabled focused harness. Initial interrupted context and resume instruction are synthetic: not evidence of continuous original startup RFI.

## Integration and remaining verification

V920 continuous handler return, V921 same-context capture/return and V922 continuous scheduler/RFI integration have separate owner workflows. V924 corrects shared OS leaf observer ownership during the V922 route; all source-only checks passed in job 139177898171. Corrected owner preflight [45606294966](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45606294966) was still running when checked. Do not claim live RFI until a same-run owner execution passes the strict V922 census. Preserve the earlier independent launch scopes.

The V923 workflow trigger now includes its own source files and relevant context/epilogue dependencies. No proprietary executable or extracted original instruction contents are recorded here.
