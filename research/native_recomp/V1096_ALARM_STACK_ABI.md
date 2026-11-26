# V1096: preserve synthetic alarm stack ABI

V1095 integration run 45754165962 refused the new six callback fixtures at alarm return (route 5, alarm 8, queue 5). The fixture changed r1 between alarm capture and return, violating the existing queue ABI witness. Map the synthetic callback stack around the already established handler stack and require r1 unchanged. Keep all production alarm and callback checks intact. Re-run the real live integration. No owner-path result is claimed.
