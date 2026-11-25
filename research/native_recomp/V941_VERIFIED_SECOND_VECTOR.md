# V941: verified original second vector and stricter witness retest

* V933 corrected owner run 45712672524, job 139551288920: 16/16 original handler tail, scheduler, loader and RFI with held second SI completion, synthetic vector stop, 8 negative controls, zero fallback.
* V938 V933 regression run 45713202078: 16/16 again.
* V938 V935 owner run 45713202154, job 139553350926: 16/16 original second vector and original trampoline after actual RFI, all 38 saved fields rewritten from poisoned fixture memory, 10 negative controls, zero fallback. SPRG omission was fixture-only; full-image V5 already implements it.

V939 installer initially matched two identical result suffixes. Narrow the patch to the exact V932 result indentation. V940 corrected audit module chain and added 16 synthetic witness cases. Retest the V939 second-vector branch/tick witness on original V935 code, using unchanged synthetic final dispatcher stop. No new continuous execution claim; full V932 still pending.
