# V84 candidate: second original STM Open acknowledged

V83 is verified, 16/16 trials. V84 reuses the authenticated V83 fixture and
the original Open and submit bodies. It preserves CPU, guest RAM, native IOS
service and previous scheduler evidence. Only request-observation counters
are reinitialized. The second original allocation, cache flush, mailbox
submission and native ACK must occur while the first descriptor remains
open. The test stops before second OSSleepThread, not after its reply.

Independent dual-mode regression 44237219737 passed 128 synthetic native
entries, 64 ACK/reply pairs and 128 generated RFI returns, reusing the same
request slot for both STM device orders without bus resets between opens.

Status: owner candidate; no second reply or OSInit completion claimed.
