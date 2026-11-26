# V1298 reply processor and IRQ-handler return contract

V1297 original-free source job has passed, including V1296 and nested-wake checks. Its original execution is queued; V1244 full image is running. No new original execution claim.

A read-only continuation contract now checks the same CPU, authenticated instruction words/branches, original return PC, two nonvolatile ABI frames, exact scheduler counter, ready queue, response header and native final Hollywood acknowledgment. Restrict the synchronous path to known IPC read/write helpers; reject other calls until the owner lane proves their necessity. No host register restore, extra IOS pump, or guest queue writes. Twelve synthetic joined cases are included; CI pending. The private metadata and owner hook integration are deliberately deferred until original wake return is verified.
