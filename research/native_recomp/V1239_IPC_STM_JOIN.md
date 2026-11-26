# V1239: same-context IPC return to STM

Admit the STM prefix only from an actual completed PostAckIpcJoin object, at the same return tick and same CPU identity. Reuse the existing V629 witness for OSInit's bridge, STM entry and first IOS_Open entry. Preserve the live mailbox snapshot and completed SI device guard, retain the IPC heap size for the next request witness, and refuse replay or altered return context. Synthetic tests model all 17 IPC calls followed by both STM path kinds; no actual IOS submission or original-game execution. CI pending.
