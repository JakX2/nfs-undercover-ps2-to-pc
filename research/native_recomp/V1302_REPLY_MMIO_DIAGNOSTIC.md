# V1302: classify original post-wake native MMIO refusal

V1300 owner run 45810945643 authenticated 265 labels and both continuation dispatch cases, compiled and reached the genuine nested wake return. Trial 0 then refused a write after 13 original instruction visits (kind=5 reason=7 gate=3). The prior V1301 full saved-context source gate passed. No new original return claim.

Separate the existing device-gate refusal into stage, boundary, alias, register, value, repeat, transport and postcondition classes. Publish only public MMIO register classes and public PPCCTRL low bits, never guest addresses, PC, original instructions or arbitrary operands. Strengthen three existing synthetic negative cases. No change to permitted hardware behavior until the owner retry identifies the actual write.

Historical V82 run 44236726199 proved that the scheduler may legitimately return first to the interrupted idle context, then disable interrupts, clear idle context and load the default thread. The next focused continuation must admit this observed route rather than requiring direct selection.
