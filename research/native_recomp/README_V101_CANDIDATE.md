# V101 verified: original SC configuration-loading body

V100 verified that the genuine native SC status callback chose
0x8051DD50. V101 restores that entire original function and preserves
its six direct dependency edges, using explicit original-callsite
guards for the first selected child 0x8051E71C or 0x8051E518.

The original GPR-save helper executes before either child. The runner
checks original thread, MSR and deferred IOS/STM state, and never
returns artificial configuration data or changes the guest branches.
The next stage must restore the selected child and identify its file
loading API before claiming SC configuration initialization.

Owner-original V101 CI run 44395679571 on 18b60db55b58e375fc733075e0f2040162ac79f8 verified all 16 original configuration-loading body entries, original GPR-save helper, and authentic selection of path builder 0x8051E71C with running thread and preserved IOS state. The body of 0x8051E71C remained unexecuted until V102.
