# V103 candidate: original asynchronous SC file-open entry

V102 owner trial 442? verified the original SC pathname copy through
0x804F1E2C. V103 restores that original wrapper and its heap getter
0x80519094 from the exact authenticated owner DOL. Its original
heap allocation and memcpy must run natively, preserving the exact
pathname bytes from prior SC preparation. The next boundary is the
authentic IOS_OpenAsync function 0x8051982C, LR 0x804F1ECC.
All 16 owner-trials must retain the deferred STM event, FS descriptor,
shutdown callbacks, SC state and running thread. The test stops before
IOS_OpenAsync writes a request or supplies any callback/return value.
A missing guest config file must not be fabricated.

Owner trial 44402480429 isolated an empty NUL-terminated SC input in the reduced guest fixture (bounded path pointer and copy destination coincide). V103 records this as `empty=1`, accepts the original error-path argument without substituting a pathname and never claims the configuration file was loaded. Real data availability remains a separate dependency.
