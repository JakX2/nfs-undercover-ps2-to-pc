# Native asynchronous STM startup: wrapper, registration and IRQ entry

## Verified owner milestones

- Deferred native IOS acceptance: run 45857155001, eight trials. IOS service step 5, pending Y2, no reply, unchanged interrupted guest CPU, original request, output and IPC ring.
- Original async submit return: run 45860818846, eight trials, 26 original instruction visits, nested restore remains masked, original caller ABI preserved.
- Original IOCTL wrapper return: run 45863068296 (bd1a7dc), eight trials, 18 original visits, 10 stack loads, nine restored nonvolatile GPRs, one masked outer dispatch poll. First owner run refused the poll; the second refused the post-poll return tick. The corrected witness permits exactly one additional outer-dispatch tick after the authenticated poll, or zero for a direct continuation. It does not relax register, memory or return identity.
- Original STM flag publication: run 45863395316 (413ed29), eight trials, seven original visits, one actual word store to the authenticated flag object, original outer restore entry, deferred IOS event held. Private geometry run 45861869190 verified eight labels, two alternative store sites for one object, zero escapes. The source contract passed 22 cases.
- Original outer restore and native third IPC exception: run 45863843475 (953a69e), eight trials, six original visits, actual mtmsr sets EE; the precise rising-EE boundary admits a hardware external exception on the active thread. CPU/SRR provenance and the native pending ACK are verified. No fifth-service reply or additional service step is generated. This owner run stops before executing the vector. All preceding owner milestones report zero interpreter fallback, complete_image=0, boot_verified=0.

## Further implementation

The active-thread dispatch contract now admits a distinct deferred-event transaction after both synchronous Opens. It requires the exact bound IOS snapshot, active context and thread identity, empty waiting queue, unchanged request, actual pending Y2 with no reply and an authenticated saved integer frame. Source run 45864147953 passed 24 cases plus the original synchronous dispatcher regression.

The new original active-vector mode (b9a7ad7) hands off the original IPC ring, credit, profile and full request to IpcDeferredAckMemory before vector execution, preserves the STM registration flag, allocator and buffers, active-context identity and thread scheduler tail, and uses the existing native SecondVectorWitness with the active caller context rather than the idle context. It deliberately retires the prior stack-frame shadow only after the actual external exception entry. Run 45864357413 is pending; no vector execution or third handler return claimed yet.

## Next bounded milestones

Authenticate the original active-context vector/trampoline save and dispatcher entry. Then execute the original IPC dispatch to handler index 27, clear Y2 and Hollywood IPC through the actual native MMIO sites, observe original mailbox credit increment and unissued-profile decrement, and return via the real active-context RFI. Do not publish a reply or invoke the deferred callback merely because the ACK cleared. The original STM routine and the complete game have not yet returned or booted.

The next optional original dispatcher mode (6299867, owner run 45864578298) is also implemented. It is gated on successful active-vector execution and the 24-case deferred dispatch contract. It permits only native PI cause/mask reads while verifying the original handler-table selection, active thread, saved integer context and preserved pending event. It stops before the IPC handler executes. Both owner checkpoints are pending at this documentation update; the last verified owner boundary remains third hardware IRQ entry.
