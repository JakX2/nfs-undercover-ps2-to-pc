#!/usr/bin/env python3
"""Private READ-ONLY owner-archive Undercover-to-Carbon DXT5 proof-of-format.

Reads original owner-supplied PS2 TRACKS ZIP and optional extracted Carbon PC
L5RB.BUN + STREAML5RB.BUN. ALL output is aggregate statistics. No original
image, proprietary hash, modified stream, game resource or executable is saved.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile
from undercover_to_pc_dxt5_bridge import (audit_undercover_section,
                                           overlay_undercover_on_existing_pc_dxt5)
from private_carbon_dxt1_stream_stage import section_span

ROW_BYTES = 92
TABLE = 0x34110
MAX_BUN = 8 * 1024 * 1024
MAX_STREAM = 128 * 1024 * 1024
MAX_SECTION = 32 * 1024 * 1024


def _path(path, max_bytes):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or not 0<p.stat().st_size<=max_bytes:
        raise ValueError('Missing, symlinked or oversized original source file')
    return p


def _private_uc_section(uc_zip, section_id):
    """Bounded ZIP CRC verification; never persist extracted copyrighted data."""
    if section_id not in (241,3401):
        raise ValueError('Unsupported Undercover section id')
    archive=_path(uc_zip, 1024 * 1024 * 1024)
    with zipfile.ZipFile(archive) as z:
        small='TRACKS/L2RB.BUN';large='TRACKS/STREAML2RB.BUN'
        if (not 0<z.getinfo(small).file_size<=MAX_BUN or
                not 0<z.getinfo(large).file_size<=MAX_STREAM):
            raise ValueError('Unsafe owner archive member size')
        bun=z.read(small)
        stream=z.read(large)  # zipfile checks the full stream's CRC
    return _slice_section(bun,stream,section_id)


def _slice_section(bun, stream, section_id):
    if not isinstance(bun,bytes) or not isinstance(stream,bytes):
        raise ValueError('Expected bounded original bundle and stream bytes')
    if not 0<len(bun)<=MAX_BUN or not 0<len(stream)<=MAX_STREAM:
        raise ValueError('Unsafe source bundle or stream size')
    sig=struct.pack('<I',TABLE)
    pos=bun.find(sig)
    if pos<0 or bun.find(sig,pos+4)>=0 or pos+8>len(bun):
        raise ValueError('Missing or ambiguous section table')
    length=struct.unpack_from('<I',bun,pos+4)[0]
    if not length or length%ROW_BYTES or pos+8+length>len(bun):
        raise ValueError('Invalid section-table row bounds')
    found=[];seen=set()
    for row in range(pos+8,pos+8+length,ROW_BYTES):
        identity=struct.unpack_from('<h',bun,row+8)[0]
        if identity in seen:
            raise ValueError('Duplicate stream section id')
        seen.add(identity)
        if identity==section_id:
            off,n=struct.unpack_from('<II',bun,row+0x14)
            if off%2048 or not 8<=n<=MAX_SECTION or off+n>len(stream):
                raise ValueError('Unsafe Undercover section span')
            found.append(stream[off:off+n])
    if len(found)!=1:
        raise ValueError('Requested Undercover section not found')
    return found[0]


def _private_pc_section(bun_path,stream_path,section_id):
    if section_id not in (141,142):
        raise ValueError('Unsupported Carbon PC section id')
    b=_path(bun_path,MAX_BUN).read_bytes()
    s=_path(stream_path,2*1024*1024*1024)
    off,n=section_span(b,s.stat().st_size,section_id)
    with s.open('rb') as f:
        f.seek(off);piece=f.read(n)
    if len(piece)!=n:
        raise ValueError('Truncated original Carbon PC section')
    return piece


def analyze_archives(uc_zip,uc_section_id=3401,max_samples=8,
                     pc_bun=None,pc_stream=None,pc_section_id=142,
                     donor_ordinal=0,pc_dxt5_ordinal=0):
    section=_private_uc_section(uc_zip,uc_section_id)
    report={'undercover_ps2_section':uc_section_id,
            'dxt5_codec':audit_undercover_section(section,max_samples)}
    if (pc_bun is None)!=(pc_stream is None):
        raise ValueError('Carbon PC bundle and stream must be supplied together')
    if pc_bun is not None:
        pc=_private_pc_section(pc_bun,pc_stream,pc_section_id)
        modified,proof=overlay_undercover_on_existing_pc_dxt5(
            pc,section,donor_ordinal,pc_dxt5_ordinal)
        if len(modified)!=len(pc) or modified==pc:
            raise ValueError('No isolated in-memory overlay')
        report['carbon_existing_slot_probe']={'section_id':pc_section_id, **proof}
    report['scope']='PRIVATE_READ_ONLY_OFFLINE_NOT_GAME_LOADED'
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',required=True,type=Path)
    p.add_argument('--undercover-section',type=int,choices=(241,3401),default=3401)
    p.add_argument('--max-samples',type=int,default=8)
    p.add_argument('--carbon-bun',type=Path)
    p.add_argument('--carbon-stream',type=Path)
    p.add_argument('--carbon-section',type=int,choices=(141,142),default=142)
    p.add_argument('--donor-ordinal',type=int,default=0)
    p.add_argument('--pc-dxt5-ordinal',type=int,default=0)
    a=p.parse_args()
    print(json.dumps(analyze_archives(a.undercover_ps2_zip,a.undercover_section,
        a.max_samples,a.carbon_bun,a.carbon_stream,a.carbon_section,
        a.donor_ordinal,a.pc_dxt5_ordinal),indent=2))

if __name__=='__main__':main()
