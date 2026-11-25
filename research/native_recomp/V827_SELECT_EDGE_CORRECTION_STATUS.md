# V827: EXISelect dependency correction

V825 owner preflight job 139045426809 refused the initial dependency assertion before translation. The V812 private census established that ordinals 5 and 6 share exactly one 32-word child, not separate mask/unmask targets. Correct the assertion to require that shared authenticated root and preserve the full caller/alias/CSR checks. Retest pending; no original select return is claimed.
