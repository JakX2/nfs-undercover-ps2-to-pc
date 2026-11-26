# V1349 submit hook prefix correction

V1348 owner run 45821059696/job 139913269549 authenticated 276 native labels, existing outer resume case and both direct call edges, then stopped at completion_hook. V651 patches the original submit continuation at 0x8051963c with an exact trace before the native tick. Permit only that known trace prefix at that one PC; preserve exact word, unique label and tick requirements, reject arbitrary prefix or mismatched trace. New synthetic coverage and bounded refusal categories. No native continuation claimed until retry.
