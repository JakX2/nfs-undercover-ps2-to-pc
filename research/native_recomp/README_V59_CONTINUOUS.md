# V59: original SIInit cold return candidate
Restores the original four controller-type requests, SITransfer and low-level immediate transfer. SHA-authenticated initialized SI data are reloaded for every independent cold boot. The normal test has zero last-transfer timestamps and a realistic 243 MHz bus-clock input, so the first type request starts immediately, with the other three queued behind it. The device model validates the original status clear, zero command and transfer control. The controller responses are not delivered; alarm scheduling and response/interrupt callbacks remain explicit failing boundaries.
 
Verification pending. This is not a complete controller implementation or game boot.
