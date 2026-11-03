"""Synthetic-only VIF PS2 packet, ADC, XYZ and UV reconstruction tests."""
import math
import struct
import unittest

from vif_strip_probe import (decode_vif, unpack_rows, decode_strip_header,
    adc_mask_from_words, candidate_triangle_indices, candidate_uvs, MAX_PACKET)


def vif_unpack(address, values, comps, bits=16, unsigned=False):
    """Create a synthetic VIF UNPACK, with source bytes, no game content."""
    if bits==32:
        size_code=0
        data=struct.pack('<'+str(len(values)*comps)+'I',
                         *(x for row in values for x in row))
    elif bits==16:
        size_code=1
        data=struct.pack('<'+str(len(values)*comps)+'H',
                         *(x & 0xffff for row in values for x in row))
    elif bits==8:
        size_code=2
        data=bytes(x & 255 for row in values for x in row)
    else:
        raise ValueError('Unsupported synthetic value width')
    cmd=0x60+((comps-1)<<2)+size_code
    imm=address | (0x4000 if unsigned else 0)
    header=struct.pack('<I', (cmd<<24) | (len(values)<<16) | imm)
    return header+data+b'\0'*((-len(data))%4)


def synthetic_packet(nv=4, suppressed=(), packbits=16, extra_color=True,
                     bad_uv=False, bad_pos=False):
    """Small finite source-free rectangle of positions/UVs and ADC flags."""
    if not 3<=nv<=32:
        raise ValueError('Fixture vertex count out of range')
    rem=nv%4
    primary=(nv-1)//4
    mask=[k in set(suppressed) for k in range(nv)]
    bits_word=0
    if nv>15 and suppressed:
        raise ValueError('Synthetic fixture only models low ADC mask bits')
    for k in range(nv):
        if mask[k]:
            bits_word|=1<<(14-k)
    expected=nv-2-sum(mask[2:])
    control=(bits_word, struct.unpack('<I',struct.pack('<f',1/256))[0],0,0)
    s=vif_unpack(0,((nv,primary,13,252),),4,8,True)
    s+=vif_unpack(1,(control,),4,32)
    box=((0.,1/256,2/256),
         (3*(nv-1)/256,(3*(nv-1)+1)/256,(3*(nv-1)+2)/256))
    b=tuple(tuple(struct.unpack('<I',struct.pack('<f',v))[0] for v in row) for row in box)
    s+=vif_unpack(2,b,3,32)
    # SoA layout: 4 vertices per group, three rows of X/Y/Z values.
    main_groups=nv//4 if rem else nv//4
    if main_groups:
        # Easier explicit rows: each lane within one group represents a vertex.
        positions=[tuple((g*4+lane)*3+a for lane in range(4))
                   for g in range(main_groups) for a in range(3)]
        if bad_pos:positions.pop()
        s+=vif_unpack(5,positions,4,packbits)
    else:
        positions=[tuple((lane)*3+a for lane in range(rem)) for a in range(3)]
        s+=vif_unpack(5,positions,rem,packbits)
    if rem and main_groups:
        s+=vif_unpack(5+3*main_groups,
                      [tuple((main_groups*4+lane)*3+a for lane in range(rem)) for a in range(3)],
                      rem,packbits)
    # In the small fixture, choose an all-16-bit ST UV encoding.
    main_uv_rows=(2*main_groups if main_groups else (nv+1)//2)
    if bad_uv:main_uv_rows=max(0,main_uv_rows-1)
    s+=vif_unpack(29,tuple((0,0,0,0) for _ in range(main_uv_rows)),4,16)
    if rem and main_groups:
        s+=vif_unpack(29+2*main_groups,tuple((0,0,0,0) for _ in range((rem+1)//2)),4,16)
    if extra_color:
        s+=vif_unpack(45,tuple((128,128,128,128) for _ in range(nv)),4,8,True)
    s+=b'\0'*((-len(s))%16)
    return s, expected


class VifPacketTests(unittest.TestCase):
    def test_four_vertices_decode(self):
        packet,np=synthetic_packet()
        result=decode_strip_header(packet,4,np)
        self.assertEqual((result['vertex_count'],result['adc_polygon_count']),(4,2))
        self.assertEqual(len(result['position_samples']),4)
        self.assertEqual(len(result['uv_samples']),4)
        self.assertEqual(result['max_bbox_error']<1,True)

    def test_three_vertex_tail_only(self):
        p,n=synthetic_packet(3)
        r=decode_strip_header(p,3,n)
        self.assertEqual((len(r['position_samples']),len(r['triangle_index_candidates'])),(3,1))

    def test_partial_position_and_uv_lanes(self):
        p,n=synthetic_packet(10)
        r=decode_strip_header(p,10,n)
        self.assertEqual((len(r['position_samples']),len(r['uv_samples'])),(10,10))

    def test_suppressed_candidate_triangle(self):
        p,np=synthetic_packet(10,suppressed=(5,))
        r=decode_strip_header(p,10,np)
        self.assertEqual((np,r['adc_polygon_count'],r['suppressed_candidate_triangles']),(7,7,1))

    def test_tail_of_three_lanes(self):
        p,n=synthetic_packet(11)
        r=decode_strip_header(p,11,n)
        self.assertEqual(len(r['uv_samples']),11)
        self.assertEqual(r['position_word_bits'],16)

    def test_bad_expected_vertex_count(self):
        p,np=synthetic_packet()
        with self.assertRaisesRegex(ValueError,'vertex count disagrees'):
            decode_strip_header(p,5,np)

    def test_bad_polygon_count(self):
        p,np=synthetic_packet()
        with self.assertRaisesRegex(ValueError,'ADC suppression'):
            decode_strip_header(p,4,np-1)

    def test_truncated_unpack_packet(self):
        raw=vif_unpack(5,tuple((1,2,3,4) for _ in range(3)),4,16)
        with self.assertRaisesRegex(ValueError,'UNPACK overreads'):
            decode_vif(raw[:-4])

    def test_unknown_command_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unrecognized'):
            decode_vif(struct.pack('<I',0x12340000))

    def test_unaligned_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'word-aligned'):
            decode_vif(b'abc')

    def test_oversize_packet_rejected(self):
        with self.assertRaisesRegex(ValueError,'excessive'):
            decode_vif(bytes(MAX_PACKET+4))

    def test_extra_uv_row_missing(self):
        p,np=synthetic_packet(10,bad_uv=True)
        with self.assertRaisesRegex(ValueError,'UV/ST main rows'):
            decode_strip_header(p,10,np)

    def test_missing_position_row(self):
        p,np=synthetic_packet(4,bad_pos=True)
        with self.assertRaisesRegex(ValueError,'position rows'):
            decode_strip_header(p,4,np)

    def test_invalid_scale(self):
        p,np=synthetic_packet()
        code=struct.pack('<I',(0x6c<<24)|(1<<16)|1)
        b=bytearray(p);at=b.index(code)
        struct.pack_into('<I',b,at+8,0)
        with self.assertRaisesRegex(ValueError,'position scale'):
            decode_strip_header(bytes(b),4,np)

    def test_nonfinite_bbox_rejected(self):
        p,np=synthetic_packet()
        code=struct.pack('<I',(0x68<<24)|(2<<16)|2)
        b=bytearray(p);at=b.index(code)
        struct.pack_into('<I',b,at+4,0x7fc00000)
        with self.assertRaisesRegex(ValueError,'Nonfinite VIF bbox'):
            decode_strip_header(bytes(b),4,np)

    def test_index_winding_candidate(self):
        self.assertEqual(candidate_triangle_indices((False,False,False,False)),
                         ((0,1,2),(2,1,3)))

    def test_adc_control_invalid(self):
        with self.assertRaisesRegex(ValueError,'Invalid VIF ADC'):
            adc_mask_from_words((0,),4,0)

    def test_vif_source_decode_unsigned(self):
        p,np=synthetic_packet()
        op=next(x for x in decode_vif(p) if x['kind']=='UNPACK' and x['address']==0)
        self.assertEqual(unpack_rows(op)[0][:2],(4,0))

    def test_flat_uv_rows(self):
        p,np=synthetic_packet()
        rows={op['address']:op for op in decode_vif(p) if op['kind']=='UNPACK'}
        self.assertEqual(candidate_uvs(rows,4,1,0),((0.,0.),)*4)

    def test_position_is_finite(self):
        p,np=synthetic_packet()
        r=decode_strip_header(p,4,np)
        self.assertTrue(all(math.isfinite(a) for vertex in r['position_samples'] for a in vertex))


if __name__=='__main__':unittest.main()
