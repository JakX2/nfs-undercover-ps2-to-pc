# V909: second original system-time call

V907 private census found four words (two stores) after OSSetAlarm's disable return, then __OSGetSystemTime; __SITransfer has three words (one load), then a conditional branch. V909 authenticates both original continuations, preserves bounded RAM checks, checks the extra load and two stores, and composes a second original system-time call using a fresh witness. The immediate branch and alarm continuation after the time return are unexecuted synthetic stops. No alarm queue or device side effects are claimed. Pending private execution.
