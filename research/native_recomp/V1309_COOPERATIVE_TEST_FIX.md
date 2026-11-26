# V1309 cooperative planner test correction

Manual inspection found the synthetic save fixture constructed 31 words instead of 32, and the intended missing stmw mutation replaced a NOP with another NOP. Correct the fixture count and the mutation, add explicit short-extent and wrong-base checks. The V1307 CI reported success, but these source inconsistencies mean its result is not sufficient to authenticate the intended coverage. Re-run corrected original-free tests. No owner fixture or device behavior changed; the pinned V1308 private retry is not restarted.
