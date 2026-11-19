# V112 candidate: nonempty original Wii SC IOS_OpenAsync request

V111 verified 16 owner-original native trials through original
IOS_OpenAsync entry for the authenticated nonempty SYSCONF path.

V112 continues through the exact original IOS_OpenAsync body:
GPR save, native request allocation, IRQ masking/restore, cache flush
and installed syscall vector. Before the native transport submits
the request, the observer verifies the actual guest IOS_Open wire
command, mode and pathname against bytes captured at V111's
original callsite, without constructing an artificial response.

This proves request construction only, not async completion,
the SC callback, full OSInit return or game boot.
Owner binaries, private logs and generated translated game code
remain inside the owner-only CI runner.
