"""Synthetic-only tests of 72-byte model hash and 96-byte instance link parser."""
import struct
import unittest
from scenery_model_hash_bridge import (parse_info_records, validate_instance_links,
    promote_model_hash0, compare_pc_to_console, summarize_scene, summarize_sources)


def record(h0=0,h1=0x123abc,h2=0x123abc,h3=0,name=b'SYNTHETIC'):
    b=bytearray(72)
    b[:len(name)]=name
    struct.pack_into('<4I',b,24,h0,h1,h2,h3)
    struct.pack_into('<f',b,0x38,10.0)
    return bytes(b)


def instances(*refs):
    out=bytearray(b'\x11'*4)
    for ref in refs:
        b=bytearray(96)
        struct.pack_into('<h',b,0x54,ref)
        out.extend(b)
    return bytes(out)


def scene(ib,refs=(0,)):
    return {'children':{0x34102:ib,0x34103:instances(*refs)}}


class InfoHashBridgeTests(unittest.TestCase):
    def test_promotes_one_record_only_slot0(self):
        b=record()
        promoted=promote_model_hash0(b)
        self.assertEqual(struct.unpack_from('<I',promoted,24)[0],0x123abc)
        self.assertEqual(b[:24]+b[28:],promoted[:24]+promoted[28:])

    def test_promotes_two_records(self):
        a=record(h1=111)+record(h1=222,name=b'OTHER')
        b=promote_model_hash0(a)
        self.assertEqual([struct.unpack_from('<I',b,i+24)[0] for i in (0,72)],[111,222])

    def test_fail_nonzero_first_slot(self):
        with self.assertRaisesRegex(ValueError,'empty-slot0'):
            promote_model_hash0(record(h0=1))

    def test_fail_zero_second_slot(self):
        with self.assertRaisesRegex(ValueError,'empty-slot0'):
            promote_model_hash0(record(h1=0))

    def test_fail_misaligned_info(self):
        with self.assertRaisesRegex(ValueError,'72-byte'):
            promote_model_hash0(record()+b'x')

    def test_empty_info_rejected(self):
        with self.assertRaisesRegex(ValueError,'72-byte'):
            parse_info_records(b'')

    def test_valid_link(self):
        self.assertEqual(validate_instance_links(instances(1,0),record()+record()),(1,0))

    def test_link_index_negative(self):
        with self.assertRaisesRegex(ValueError,'invalid info index'):
            validate_instance_links(instances(-1),record())

    def test_link_index_too_high(self):
        with self.assertRaisesRegex(ValueError,'invalid info index'):
            validate_instance_links(instances(1),record())

    def test_wrong_instance_prefix(self):
        with self.assertRaisesRegex(ValueError,'96-byte'):
            validate_instance_links(b'\0'*4+instances(0)[4:],record())

    def test_wrong_instance_stride(self):
        with self.assertRaisesRegex(ValueError,'96-byte'):
            validate_instance_links(instances(0)+b'X',record())

    def test_empty_instance_table(self):
        with self.assertRaisesRegex(ValueError,'Empty instance'):
            validate_instance_links(b'\x11'*4,record())

    def test_nontrivial_info_refs(self):
        s=scene(record()+record(),(1,0,1))
        r=summarize_scene(s)
        self.assertEqual(r['instances'],3)
        self.assertEqual(r['valid_instance_to_info_links'],3)
        self.assertEqual(r['distinct_info_targets'],2)
        self.assertEqual(r['links_equal_to_instance_ordinals'],0)

    def test_target_pc_matching_control(self):
        donor=scene(record(),(0,))
        pc=scene(promote_model_hash0(record()),(0,))
        c=compare_pc_to_console({42:pc},{42:donor})
        self.assertEqual(c['exact_info_payloads_after_slot0_copy'],1)
        self.assertEqual(c['exact_info_payloads_without_promotion'],0)

    def test_target_pc_detects_nonhash_difference(self):
        donor=scene(record(),(0,))
        bad=bytearray(promote_model_hash0(record()))
        bad[60]=0x99
        c=compare_pc_to_console({42:scene(bytes(bad), (0,))},{42:donor})
        self.assertEqual(c['exact_info_payloads_after_slot0_copy'],0)

    def test_different_root_info_counts_excluded(self):
        a={42:scene(record()+record(),(0,1))}
        b={42:scene(record(),(0,))}
        self.assertEqual(compare_pc_to_console(a,b)['same_number_of_info_records'],0)

    def test_summary_first_slot_counts(self):
        r=summarize_sources({42:scene(record()+record(h1=333,h3=44),(1,0))})
        self.assertEqual(r['info_records'],2)
        self.assertEqual(r['fourth_model_hash_nonzero'],1)


if __name__ == '__main__':
    unittest.main()
