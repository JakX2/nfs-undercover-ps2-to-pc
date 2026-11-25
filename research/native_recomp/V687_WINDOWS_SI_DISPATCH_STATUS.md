# V687: advance default complete original Windows scope to SI dispatch

V678 Windows run 45518876619 passed all six external exception stages with full original MSVC x64 link. The original Linux dispatcher run 45522042241 independently passed all six dispatcher stages; V684 reached and returned from the first original helper. Therefore promote Windows default to os-si-dispatch, preserving all earlier explicit scopes, and verify the original handler selection on Windows using the same observers. This promotion is not yet a Windows handler execution claim. No new proprietary content.
