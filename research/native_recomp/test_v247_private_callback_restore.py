#!/usr/bin/env python3
"""V247 original-free exact placeholder restoration and private isolation."""
import re
import subprocess
import struct
import tempfile
import unittest
from pathlib import Path
from extend_private_text import NOP, STUB, install
from restore_v247_private_callbacks import SPANS, select_patches, PatchError
from derive_v247_private_callback_restore_runner import derive as runner, PATTERN, FAIL
HERE=Path(__file__).resolve().parent

def synthetic_pair():
    header=bytearray(256)
    fixture=bytearray(header)
    owner=bytearray(header)
    for slot,(key,(address,size)) in enumerate(SPANS.items()):
        off=256+sum(n for _,n in list(SPANS.values())[:slot])
        for hdr,value in ((0,off),(0x48,address),(0x90,size)):
            struct.pack_into(">I",fixture,hdr+4*slot,value)
            struct.pack_into(">I",owner,hdr+4*slot,value)
        fixture.extend(STUB+NOP*(size//4-2))
        owner.extend(bytes((0x12,0x34,0x56,0x78))*(size//4))
    return bytes(owner),bytes(fixture)

class V247(unittest.TestCase):
    def test_only_authentic_or_synthetic_words_may_be_replaced(self):
        own,old=synthetic_pair()
        patches,changed,flags=select_patches(own,old)
        self.assertEqual(len(patches),2)
        self.assertEqual(changed,{"cb":True,"nand":True})
        self.assertTrue(flags[0] and flags[1])
        restored=install(old,patches)
        for address,current,original in patches:
            self.assertEqual(len(current),len(original))
            self.assertEqual(original,
                __import__("make_osinit_execparams_v28").text_at(
                    restored,address,len(original)))
        inverted=install(restored,[(a,original,current)
                                  for a,current,original in patches])
        self.assertEqual(inverted,old)
        with self.assertRaises(PatchError):
            select_patches(own,b"short")
        bad=bytearray(old)
        bad[256:260]=bytes((170,187,204,221))
        with self.assertRaises(PatchError) as error:
            select_patches(own,bytes(bad))
        self.assertEqual(error.exception.stage,"select")
        self.assertEqual(error.exception.kind,"foreign")

    def test_shaped_private_runner_and_no_raw_generated_data(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for mark in ("V245_SC_AOT_MAP verified=1",
                     "restore_v247_private_callbacks.py",
                     "V247_SC_PRIVATE_CALLBACK_RESTORE verified=1"):
            self.assertIn(mark,script)
        self.assertIn('"$work/v247-restore.log")" -eq 1',script)
        self.assertIn("V247_RESTORE_FAIL",script)
        self.assertNotIn("cat \"$work/private.dol\"",script)
        for file in ("restore_v247_private_callbacks.py",
                     "derive_v247_private_callback_restore_runner.py"):
            src=(HERE/file).read_text()
            self.assertNotIn("print(text_at(",src)
            self.assertNotIn("print(original",src)
        good="V247_CALLBACK_RESTORE auth=1 cb_safe=1 nand_safe=1 cb_changed=1 nand_changed=1 nop=1 stub=1 original=1 restored=1 reversible=1"
        self.assertIsNotNone(re.fullmatch(PATTERN,good))
        self.assertIsNone(re.fullmatch(PATTERN,good+" original_bytes=private"))
        self.assertIsNotNone(re.fullmatch(FAIL,"V247_RESTORE_FAIL stage=select kind=foreign"))
        wf=(HERE.parents[1]/".github/workflows/wii-v247-private-callback-restore.yml").read_text()
        for mark in ("run_v247_private_callback_restore.sh",
                     "test_v247_private_callback_restore.py",
                     "V247_SC_PRIVATE_CALLBACK_RESTORE verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as temp:
            for name,s in (("runner",script),("wrapper",
                    (HERE/"run_v247_private_callback_restore.sh").read_text())):
                p=Path(temp)/name;p.write_text(s,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
