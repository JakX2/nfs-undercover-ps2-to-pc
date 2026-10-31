#!/usr/bin/env python3
"""Optional GLB preview of OFFLINE native PC objects; not a game asset installer."""
from pathlib import Path
import sys
import numpy as np
import trimesh
from carbon_pc_identity_v27 import root_parts
from carbon_pc_scenery_v19 import parse_component

root=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else Path('samples/RedBuilding_1B_1C_1Z_Native_PC_V41.chunk').read_bytes()
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('samples')
out.mkdir(parents=True,exist_ok=True)
for e in root_parts(root)['entries']:
    m=parse_component(e['bytes'],8,len(e['bytes']))
    if m['name'].endswith('_1B_00'): continue # The 1B preview was already delivered in V20.
    vertices=np.array([(x,z,-y) for x,y,z in m['positions']],dtype=np.float32)
    faces=np.array(m['faces'],dtype=np.int64)
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    mesh.visual.vertex_colors=np.array(m['colors'],dtype=np.uint8)
    dest=out/(m['name']+'_PC_NativeFormat_V41.glb')
    mesh.export(dest)
    reread=trimesh.load(dest,force='mesh')
    assert len(reread.faces)==len(m['faces']) and len(reread.vertices)==len(m['positions'])
    print(dest.name, len(reread.vertices),len(reread.faces),dest.stat().st_size)
