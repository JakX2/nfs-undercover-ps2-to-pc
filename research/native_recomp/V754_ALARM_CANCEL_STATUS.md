# V754: original OSCancelAlarm native queue operations

V749 authenticated the 70-word original cancellation root, with existing disable/restore dependencies and a possible timer reprogramming route via system time and three two-word calls. V754 focuses on original inactive, middle, tail and singleton cancellation paths with synthetic alarm nodes, verified queue SDA identity, full native instruction audit, exact direct edges, queue link/handler checks and canaries. The head-with-successor case intentionally refuses at the system-time dependency before it executes. No timer reprogramming, original SI handler path or continuous boot is claimed. Owner CI pending.

## V759 queue-address correction

V754 owner preflight run 45549178660 refused the direct-only SDA-store shape. Use conservative forward constant tracking from the established original SDA base, including computed addresses and ABI clobbering across calls. Require both known queue addresses to be reached by actual store instructions and report only bounded counts. The fixture uses the established original SDA base so absolute addresses and SDA-relative addresses agree. Synthetic tests cover computed/volatile/merged addresses. Original cancellation execution remains pending.
