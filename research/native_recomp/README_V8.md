# Undercover Wii Resource Bridge V8

Original-free code for investigating Wii disc path lookup and extracted game assets. Intended for the private owner-original Undercover Wii port research under PR #36. Not a playable native port.

## Reproduce without any game files

Linux / MSYS2 with C++20:

```bash
c++ -std=c++20 -O2 -I . test_guest_disc_paths_v8.cpp -o test_guest_disc_paths_v8
./test_guest_disc_paths_v8 ./synthetic-disc
python3 test_resource_audit_v8.py
```

## Apply to a local copy of NWiiRecomp

```bash
python3 apply_guest_disc_paths_v8.py /path/to/NWiiRecomp-master
```

The script adds `nWiiRuntime/include/runtime/guest_disc_paths.h` and patches only the `DVDOpen` host filepath construction and guest-string limit. Reapplying it should report `DVDOpen source changed: False`. This does not patch other DI/IOS/FST read paths, and is not a standalone fix for native boot.

## Read-only resource audit

```bash
python3 audit_wii_disc_resources_v8.py GLOBAL.7z FRONTEND.7z CREDITS.zip MEMCARD.zip MOVIES.zip
```

The script checks filenames and uncompressed lengths without unpacking resource bytes. On Windows it calls the installed `7z`/`7za`/`7zz` executable to list `.7z` entries; Linux can also use libarchive. For a currently extracted folder such as `D:\NFS`, inspect it directly:

```powershell
python .\audit_wii_disc_resources_v8.py 'D:\NFS'
```

**Use your own game disc and extracted assets.** This toolkit does not include original content or a `ZDIR.bin` substitute.
