# IPC ring dispatch contract

Verified prior original native profiling return: run 45849960908, eight trials, 41 instruction visits and four profile stores per trial, with the original ring and request preserved. Source witness run 45849598881 passed 42 cases.

The older SDK reconstruction in zeldaret/tp, libs/revolution/src/ipc/ipcclt.c, suggests a send operation writes the request physical address to PPCMSG, advances the read pointer and count, decrements mailbox credit, then writes PPCCTRL. The independent single-request observer tests those three exact memory updates, permits no unrelated ring/request changes, and requires externally authenticated device-write observations. It does not write memory, implement IOS service, or fabricate an available credit. Ring and credit object identity, actual store sites, exact branch paths, and actual device integration are not yet established for this next lane. Source-only CI pending.
