#!/usr/bin/env python3
"""Original-free ZIP and extracted-directory tests for V8 resource audit."""
import tempfile
from pathlib import Path
import zipfile
from audit_wii_disc_resources_v8 import normalized, inspect

assert normalized('ExtractGLOBAL\\GAMEPLAY.BIN') == 'GLOBAL/GAMEPLAY.BIN'
assert normalized('GLOBAL/../secret') is None
assert normalized('C:/Windows/something') is None
assert normalized('MOVIES//file') is None
with tempfile.TemporaryDirectory() as root:
    root = Path(root)
    archive = root/'FRONTEND.zip'
    with zipfile.ZipFile(archive, 'w') as f:
        f.writestr('FRONTEND/FRONTB1.BUN', b'fixture')
        f.writestr('FRONTEND/LOGOS.BIN', b'a')
        f.writestr('../outside.txt', b'evil')
    folder = root/'ExtractGLOBAL'
    folder.mkdir()
    (folder/'GAMEPLAY.BIN').write_bytes(b'123')
    res=inspect([archive,folder], ['FRONTEND\\FRONTB1.BUN','GLOBAL/GAMEPLAY.BIN','NFS/ZDIR.BIN'])
    assert res['file_entries'] == 3, res
    assert res['sum_uncompressed_bytes'] == 11, res
    assert res['rejected_archive_paths'] == 1, res
    assert res['expected'] == {'FRONTEND\\FRONTB1.BUN':True,'GLOBAL/GAMEPLAY.BIN':True,'NFS/ZDIR.BIN':False}, res
print('PASS: 8 resource-audit assertions with synthetic ZIP and directory data')
