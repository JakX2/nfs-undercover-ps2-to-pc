# V1131: authenticate GQR state at both native RFI polls

The live epilogue witness previously compared GQRs at the pre-RFI boundary and final resumed instruction only. Third ACK RFI deliberately stops earlier, after two same-tick polls. Check the original loader-derived expected GQR array on both polls; retain existing integer-state and device ownership checks. No synthetic writes in the runtime. Remove the weaker redundant poll-to-poll snapshot. Existing focused and synthetic tests must reverify this change.
