# V57: EXIInit original return candidate
Extends V56 from 0x804EFAB4 through the original remaining EXIInit branch sequence. Tests a no-removable-card configuration and both original EXIProbe calls. The original version-registration wrapper receives the version pointer from SHA-authenticated initialized data; OSReport is an explicitly bounded returning test sink. The next OSInit service at 0x805208C8 is still a synthetic stop. Card-present timing and special-device paths are explicitly guarded and not claimed working.
 
Verification pending until the focused owner CI run completes. This is not a complete game boot.
