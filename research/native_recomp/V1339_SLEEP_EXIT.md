# V1339: original nested interrupt restore and OSSleepThread return contract

Capture the real pre-sleep caller stack and nonvolatile ABI at original OSSleepThread entry. From the V1336 restored sleeping caller, observe the original nested restore leaf, require one MSR write retaining EE=0, exact inline return to sleep, original sleep epilogue restoring caller ABI, and outer dispatch to the original synchronous submit continuation. Nine synthetic cases. No new guest writes or owner execution yet. The V1337/V1338 private completion geometry preparation remains separate.
