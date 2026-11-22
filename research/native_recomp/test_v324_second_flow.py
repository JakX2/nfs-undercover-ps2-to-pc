#!/usr/bin/env python3
"""V324 synthetic-only branch/link and ELF symbol-window tests."""
import hashlib
import unittest

from analyze_v324_second_flow import TARGETS,inspect,analyze_word_window

ELF=b"synthetic ELF without proprietary code"
PC=TARGETS[0]

def parser(_):
    funcs={x:16 for x in TARGETS}
    # 0x80545100 is an interior target, 4 bytes into its parent.
    funcs.pop(TARGETS[3])
    funcs[TARGETS[3]-4]=20
    return funcs

def reader(_,pc,n):
    if n!=4:
        raise ValueError("unexpected window")
    if pc==TARGETS[0]:
        return [0x48000101,0x41820008,0x4e800020,0x60000000]
    if pc==TARGETS[1]:
        return [0x48000001,0x4e800020,0x60000000,0x60000000]
    return [0x60000000,0x60000000,0x60000000,0x4e800020]

def run(symbol_parser=parser):
    return inspect(
        ELF,digest=hashlib.sha256(ELF).hexdigest(),
        parser=symbol_parser,word_reader=reader
    )

class Tests(unittest.TestCase):
    def test_five_authenticated_function_windows_and_calls(self):
        lines=run()
        self.assertIn("targets=5 exact=4 interior=1 unknown=0 calls=2",lines[0])
        self.assertIn(
            f"V324_FLOW pc={PC:08x} kind=exact words=4 calls=1 targets=1 cond=1 "
            "local=0 bclr=1 bcctr=0 conditional_calls=0",lines[1]
        )
        self.assertIn(
            f"V324_CALLEE from={PC:08x} rank=1 to={PC+0x100:08x} calls=1",lines[2]
        )
        self.assertTrue(any(
            "pc=80545100 kind=interior words=4" in line for line in lines
        ))

    def test_ninth_original_callee_not_dropped(self):
        # The authenticated 144-word IOS-request function has nine
        # distinct callees. Truncating at eight loses a real dependency.
        def symbols(_):
            return {PC:40}
        def nine_words(_,pc,n):
            if pc!=PC or n!=10:
                raise ValueError("wrong read window")
            return [0x48000101+i*0x100 for i in range(9)]+[0x4e800020]
        lines=inspect(
            ELF,digest=hashlib.sha256(ELF).hexdigest(),
            parser=symbols,word_reader=nine_words
        )
        self.assertIn("targets=5 exact=1 interior=0 unknown=4 calls=9",lines[0])
        direct=[line for line in lines if line.startswith(
            f"V324_CALLEE from={PC:08x} "
        )]
        self.assertEqual(len(direct),9)
        self.assertTrue(any("rank=9" in line for line in direct))

    def test_branch_geometry_and_conditional_calls(self):
        cond,local,bclr,bcctr,cond_calls,targets=analyze_word_window(
            PC,[0x41820009,0x48000004,0x4e800420,0x4e800020]
        )
        self.assertEqual(cond,1)
        self.assertEqual(cond_calls,1)
        self.assertEqual(bcctr,1)
        self.assertEqual(bclr,1)
        self.assertEqual(local,1)
        self.assertTrue(targets)

    def test_unknown_target_not_assigned_fake_size(self):
        lines=run(lambda _:{PC:16})
        self.assertIn("exact=1 interior=0 unknown=4",lines[0])
        self.assertTrue(any("kind=unknown words=0" in line for line in lines))

    def test_no_words_or_private_paths_in_output(self):
        text="\n".join(run())
        self.assertNotIn("synthetic ELF",text)
        self.assertNotIn("0x48000101",text)
        self.assertNotIn("original opcodes",text)

    def test_reject_wrong_sha_and_word_geometry(self):
        with self.assertRaisesRegex(ValueError,"authenticated_digest"):
            inspect(ELF)
        with self.assertRaisesRegex(ValueError,"word_geometry"):
            analyze_word_window(PC,[])
        with self.assertRaisesRegex(ValueError,"word_geometry"):
            analyze_word_window(PC,[-1,0,0,0])

if __name__=="__main__":
    unittest.main()
