#!/usr/bin/env python3
"""V274 original-free SC writer input load/branch provenance tests."""
import unittest
from pathlib import Path
from audit_v274_sc_input_loads import classify_source,classify_function,audit

BASE=0x80530ba0
def instr(op,rt,ra,imm):
    return op<<26|rt<<21|ra<<16|(imm&0xffff)
def mr(ra,src):
    return (31<<26)|(src<<21)|(ra<<16)|(src<<11)|(444<<1)
def store(rs):
    return instr(38,rs,13,-3176)

class Tests(unittest.TestCase):
    def test_stack_load_through_register_copy(self):
        instructions=[instr(32,4,1,-8),mr(5,4),store(5)]+[0x60000000]*8
        result=classify_source(instructions,2,5)
        self.assertEqual(result,("load","word","stack",-8,0,1))
        rows=classify_function(BASE,instructions)
        self.assertEqual(len(rows),1)
        self.assertIn("kind=load width=word base=stack disp=-8",rows[0])

    def test_status_sda_and_indirect_pointer(self):
        words=[instr(34,5,13,-3176),store(5)]
        self.assertEqual(classify_source(words,1,5),
                         ("status","byte","sda",-3176,0,0))
        words=[instr(34,6,10,4),store(6)]
        self.assertEqual(classify_source(words,1,6),
                         ("load","byte","pointer",4,0,0))
        words=[instr(14,6,0,1),store(6)]
        self.assertEqual(classify_source(words,1,6),
                         ("constant","none","none",1,0,0))

    def test_guards_fail_closed(self):
        words=[instr(34,5,1,4),0x48000005,store(5)]
        self.assertEqual(classify_source(words,2,5)[0],"branch")
        words=[instr(34,5,1,4),0x7c0002a6,store(5)]
        self.assertEqual(classify_source(words,2,5)[0],"unknown")
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify_source(words,14,5)
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not owner Wii executable")

    def test_owner_private_workflow(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v274-sc-input-loads.yml").read_text(encoding="utf-8")
        self.assertIn("V274_INPUT_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
